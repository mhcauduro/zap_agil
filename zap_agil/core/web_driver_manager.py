"""
Gerencia a inicialização, configuração, otimização e encerramento do WebDriver,
comunicando-se com o sistema via notificações e aplicando técnicas anti-detecção.
"""

import time
import traceback
from typing import TYPE_CHECKING

from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from zap_agil.utils.logging_config import logging

from .bot_locators import WhatsAppLocators as Locators
from .constants import THEME_COLORS, CampaignState, ConnectionState

if TYPE_CHECKING:
    from .bot_service import BotService
try:
    import pygetwindow as gw
except ImportError:
    gw = None


class WebDriverManager:
    """
    Gerencia a conexão do WebDriver com o WhatsApp Web, aplicando técnicas de anti-detecção,
    restauração de janela sem roubo de foco e definição de título personalizado para acessibilidade.
    """

    def __init__(self, bot_service: "BotService"):
        self.bot_service = bot_service
        self.driver: webdriver.Chrome | None = None
        logging.debug("WebDriverManager inicializado.")

    def _set_window_title(self, title: str = "Whatsapp Bot") -> None:
        """
        Tenta definir o título da janela do Chrome para o valor especificado.
        Isso facilita a identificação e manipulação da janela, além de melhorar a acessibilidade.
        """
        if not gw:
            return
        try:
            # Procura janelas do Chrome abertas
            chrome_windows = [w for w in gw.getWindowsWithTitle("Chrome") if w.title]
            for win in chrome_windows:
                if title not in win.title:
                    win.title = title
            logging.debug(f"Título da janela do Chrome ajustado para '{title}'.")
        except Exception as e:
            logging.warning(f"Não foi possível definir o título da janela do Chrome: {e}")

    def restore_chrome_window_without_focus(self) -> None:
        """
        Restaura a janela do Chrome (se minimizada) sem trazê-la para frente
        ou roubar o foco do usuário.
        Também tenta garantir que o título da janela seja sempre "Whatsapp Bot" para acessibilidade.
        Utiliza pygetwindow para manipulação robusta de janelas no Windows.
        """
        if not gw:
            # Notifica apenas uma vez se a biblioteca estiver faltando
            if not hasattr(self, "_pygetwindow_notified"):
                self.bot_service._notify(
                    "log",
                    "pygetwindow não instalado. Funcionalidade de restaurar janela desativada.",
                    THEME_COLORS["log_warning"],
                )
                logging.warning("pygetwindow não instalado. Função de restaurar janela desativada.")
                self._pygetwindow_notified = True
            return

        try:
            # Sempre tenta renomear as janelas antes de restaurar
            self._set_window_title()
            # Procura janelas minimizadas com o título "Whatsapp Bot"
            chrome_windows = [w for w in gw.getWindowsWithTitle("Whatsapp Bot") if w.isMinimized]
            if not chrome_windows:
                return
            for win in chrome_windows:
                # Minimiza e restaura para garantir que não roube o foco
                win.minimize()
                win.restore()
            logging.debug(f"Janelas do Chrome restauradas sem foco: {len(chrome_windows)}")
        except Exception as e:
            self.bot_service._notify(
                "log",
                f"Não foi possível restaurar a janela do Chrome: {e}",
                THEME_COLORS["log_warning"],
            )
            logging.error(f"Erro ao restaurar janela do Chrome: {e}")

    def initialize_driver(self, headless: bool = False) -> None:
        """
        Prepara as configurações do Chrome, inicia o WebDriver e gerencia o processo de login.
        Após a inicialização, define o título da janela para "Whatsapp Bot"
        e garante acessibilidade.

        Args:
            headless (bool): Se True, executa o Chrome em modo invisível (sem interface gráfica).
        """
        if self.driver:
            self.bot_service._notify(
                "log", "O WebDriver já está inicializado.", THEME_COLORS["log_warning"]
            )
            logging.info("Tentativa de inicializar WebDriver já existente.")
            return

        self.bot_service.connection_state = ConnectionState.CONNECTING
        self.bot_service._notify("connection_status", self.bot_service.connection_state)
        self.bot_service._notify(
            "log", "Iniciando conexão com o WhatsApp...", THEME_COLORS["log_info"]
        )
        logging.info("Iniciando conexão com o WhatsApp Web.")

        try:
            logging.debug("Configurando opções do ChromeDriver.")
            # --- configurações antidetexão otimizadas ---
            profile_path = self.bot_service.app_data_dir / "Chrome_Profile_ZapAgil"
            options = webdriver.ChromeOptions()

            # 1. Cria um perfil do chrome na pasta appdata do bot,
            #    para manter o whatsapp logado e não ter que escanear o QR sempre.
            options.add_argument(f"--user-data-dir={profile_path}")

            # 2. Atualiza o User-Agent
            options.add_argument(
                "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.7204.97 Safari/537.36"
            )

            # 3. Configurações de otimização e compatibilidade adicionais
            options.add_argument("--start-maximized")
            options.add_argument("--log-level=3")
            options.add_argument("--disable-gpu")
            options.add_argument("--disable-infobars")
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-popup-blocking")
            options.add_argument("--disable-notifications")
            options.add_argument("--disable-background-timer-throttling")
            options.add_argument("--disable-backgrounding-occluded-windows")
            options.add_argument("--disable-renderer-backgrounding")
            if headless:
                options.add_argument("--headless=new")
                options.add_argument("--disable-software-rasterizer")

            # 4. Remover flags pra não detectar automação
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option("useAutomationExtension", False)
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--disable-dev-shm-usage")

            # 5. Performance, desativa carregamento de imagens
            prefs = {"profile.managed_default_content_settings.images": 2}
            options.add_experimental_option("prefs", prefs)

            # --- Iniciar o Driver
            driver_path = ChromeDriverManager().install()
            service = ChromeService(executable_path=driver_path)

            self.driver = webdriver.Chrome(service=service, options=options)
            logging.info("ChromeDriver inicializado com sucesso.")

            # Após inicializar, tenta definir o título da janela
            self._set_window_title()

            # 6. Ingetando javascript antidetexão
            self.driver.execute_cdp_cmd(
                "Page.addScriptToEvaluateOnNewDocument",
                {
                    "source": """
                        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                        Object.defineProperty(navigator, 'languages', {get: () => ['pt-BR', 'pt']});
                        Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});
                        window.chrome = { runtime: {} };
                        Object.defineProperty(navigator, 'platform', {get: () => 'Win32'});
                        Object.defineProperty(navigator, 'vendor', {get: () => 'Google Inc.'});
                    """
                },
            )

            # Lógica inteligente para conexão com o whatsapp
            self.driver.get("https://web.whatsapp.com")
            self.bot_service._notify("status_update", "Aguardando página do WhatsApp...")
            logging.debug("Aguardando página do WhatsApp carregar.")

            # Após carregar a página, tenta novamente garantir o título correto
            self._set_window_title()

            qr_found = False
            session_found = False

            # Espera pelo QR Code ou caixa de pesquisa e detecta o que vier primeiro
            try:
                wait = WebDriverWait(self.driver, 45)
                wait.until(
                    lambda d: (
                        d.find_element(By.XPATH, Locators.QR_CODE_CONTAINER)
                        if self._element_exists(By.XPATH, Locators.QR_CODE_CONTAINER)
                        else (
                            d.find_element(By.XPATH, Locators.SEARCH_BAR)
                            if self._element_exists(By.XPATH, Locators.SEARCH_BAR)
                            else None
                        )
                    )
                )

                # Decide qual elemento foi encontrado
                if self._element_exists(By.XPATH, Locators.QR_CODE_CONTAINER):
                    qr_found = True
                    logging.debug("QR Code detectado na tela do WhatsApp Web.")
                elif self._element_exists(By.XPATH, Locators.SEARCH_BAR):
                    session_found = True
                    logging.debug("Sessão anterior do WhatsApp Web detectada.")

            except TimeoutException:
                # Nenhum dos dois foi encontrado em 45s
                self.bot_service._notify(
                    "log",
                    "Tempo esgotado: Não foi possível identificar QR Code ou barra de pesquisa.",
                    THEME_COLORS["log_error"],
                )
                raise

            if qr_found:
                # QR Code detectado
                self.bot_service.connection_state = ConnectionState.NEEDS_QR_SCAN
                self.bot_service._notify("connection_status", self.bot_service.connection_state)
                self.bot_service._notify(
                    "log",
                    "Escaneie o QR Code para continuar.",
                    THEME_COLORS["log_warning"],
                )

                # Espera até usuário escanear QR, QR desaparecer
                try:
                    WebDriverWait(self.driver, 180).until_not(
                        ec.visibility_of_element_located((By.XPATH, Locators.QR_CODE_CONTAINER))
                    )
                    logging.info("QR Code escaneado com sucesso.")
                except TimeoutException:
                    self.bot_service._notify(
                        "log",
                        "Tempo esgotado: QR Code não foi escaneado.",
                        THEME_COLORS["log_error"],
                    )
                    logging.error("Tempo esgotado: QR Code não foi escaneado.")
                    raise

                # Após escaneio, espera a barra de pesquisa aparecer
                self.bot_service._notify("status_update", "Conectando e carregando conversas...")
                try:
                    WebDriverWait(self.driver, 45).until(
                        ec.presence_of_element_located((By.XPATH, Locators.SEARCH_BAR))
                    )
                    logging.info("Barra de pesquisa do WhatsApp carregada após login.")
                except TimeoutException:
                    self.bot_service._notify(
                        "log",
                        "Erro: Barra de pesquisa não apareceu após login.",
                        THEME_COLORS["log_error"],
                    )
                    logging.error("Barra de pesquisa não apareceu após login.")
                    raise

            elif session_found:
                # Sessão já logada, barra de pesquisa encontrada rapidamente
                self.bot_service._notify(
                    "log",
                    "Sessão anterior encontrada. Já conectado ao WhatsApp.",
                    "gray",
                )
                self.bot_service._notify("status_update", "Conectando e carregando conversas...")
                logging.info("Sessão anterior do WhatsApp Web restaurada.")

            # Sucesso!
            self.bot_service.connection_state = ConnectionState.CONNECTED
            self.bot_service._notify("connection_status", self.bot_service.connection_state)
            self.bot_service._notify(
                "log",
                "Conexão com o WhatsApp estabelecida com sucesso.",
                THEME_COLORS["log_success"],
            )
            self.bot_service._notify("status_update", "Conectado")
            logging.info("Conexão com o WhatsApp Web estabelecida.")

        except Exception as e:
            self.bot_service.connection_state = ConnectionState.FAILED
            self.bot_service._notify("connection_status", self.bot_service.connection_state)
            self.bot_service._notify(
                "log",
                f"ERRO CRÍTICO: Falha ao iniciar ou conectar: {e}\n{traceback.format_exc()}",
                THEME_COLORS["log_error"],
            )
            logging.error(f"Falha ao iniciar ou conectar WebDriver: {e}\n{traceback.format_exc()}")
            self.shutdown()

    def shutdown(self) -> None:
        """
        Encerra o WebDriver de forma segura, liberando recursos e notificando o usuário.
        """
        if self.driver:
            try:
                self.driver.quit()
                time.sleep(1)
                logging.info("WebDriver encerrado com sucesso.")
            except Exception as e:
                self.bot_service._notify("log", f"Erro menor ao fechar o driver: {e}", "gray")
                logging.warning(f"Erro menor ao fechar o driver: {e}")
            finally:
                self.driver = None
                self.bot_service.connection_state = ConnectionState.DISCONNECTED
                self.bot_service._notify("connection_status", self.bot_service.connection_state)
                self.bot_service._notify("log", "Sessão do navegador encerrada.", "gray")

    def is_whatsapp_ready(self) -> bool:
        """
        Verifica se a interface principal do WhatsApp está carregada e pronta para uso.
        """
        if not self.driver or not getattr(self.driver, "session_id", None):
            return False
        try:
            ready = self.driver.find_element(By.XPATH, Locators.SEARCH_BAR).is_displayed()
            logging.debug(f"WhatsApp pronto: {ready}")
            return ready
        except (NoSuchElementException, WebDriverException):
            logging.debug("WhatsApp não está pronto para uso.")
            return False

    def handle_disconnection(self) -> bool:
        """
        Tenta reconectar automaticamente em caso de desconexão durante uma campanha.
        """
        self.bot_service._notify(
            "log",
            "Conexão perdida! Tentando reconectar...",
            THEME_COLORS["log_warning"],
        )
        logging.warning("Conexão perdida! Tentando reconectar...")
        for i in range(3):
            if self.bot_service.campaign_state == CampaignState.STOPPED:
                logging.info("Reconexão abortada: campanha parada.")
                return False

            self.bot_service._notify(
                "log", f"Tentativa de reconexão {i + 1}/3... Aguardando 10s...", "gray"
            )
            logging.debug(f"Tentativa de reconexão {i + 1}/3...")
            time.sleep(10)
            if self.is_whatsapp_ready():
                self.bot_service._notify(
                    "log", "Conexão reestabelecida!", THEME_COLORS["log_success"]
                )
                logging.info("Conexão reestabelecida!")
                return True

        self.bot_service._notify(
            "log", "FALHA: Não foi possível reconectar.", THEME_COLORS["log_error"]
        )
        logging.error("FALHA: Não foi possível reconectar ao WhatsApp Web.")
        return False

    def _element_exists(self, by: str, value: str) -> bool:
        """
        Retorna True se o elemento existe na página, False caso contrário.
        Antes de buscar, garante que a janela do Chrome esteja restaurada e acessível.
        """
        self.restore_chrome_window_without_focus()
        if not self.driver or not getattr(self.driver, "session_id", None):
            return False
        try:
            element = self.driver.find_element(by, value)
            exists = element.is_displayed()
            logging.debug(f"Elemento '{value}' existe: {exists}")
            return exists
        except Exception:
            logging.debug(f"Elemento '{value}' não encontrado.")
            return False
