"""
Gerencia todas as interações diretas com a interface do WhatsApp Web via Selenium,
de forma robusta, otimizada e com feedback claro para o sistema.
"""

from __future__ import annotations

import random
import re
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any

from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

from zap_agil.utils.logging_config import logging

from .bot_locators import WhatsAppLocators as Locators
from .constants import (
    HUMAN_TYPING_DELAY_MAX,
    HUMAN_TYPING_DELAY_MIN,
    PHONE_COUNTRY_CODE,
    THEME_COLORS,
)

if TYPE_CHECKING:
    from .bot_service import BotService


class WhatsAppManager:
    """
    Gerencia interações com o WhatsApp Web.
    """

    def __init__(self, bot_service: BotService) -> None:
        logging.debug("WhatsAppManager inicializado.")
        """
        :param bot_service: Instância de BotService responsável pela orquestração do bot.
        """
        self.bot_service = bot_service

    @property
    def driver(self) -> WebDriver:
        """
        Obtém a instância atual e ativa do WebDriver,
        lançando um erro se não estiver disponível.
        """
        driver = getattr(self.bot_service.webdriver_manager, "driver", None)
        if not driver or not getattr(driver, "session_id", None):
            logging.error("Driver do Chrome não disponível ou encerrado.")
            raise WebDriverException(
                "O driver do Google Chrome não está disponível ou foi encerrado."
            )
        return driver

    def _wait_for_element(self, by: str, value: str, timeout: int = 10) -> Any:
        """
        Espera por um elemento no DOM, restaurando a janela do Chrome antes da busca
        e notificando em caso de falha.
        """
        # Garante que a janela do Chrome não está minimizada
        if hasattr(self.bot_service, "webdriver_manager") and hasattr(
            self.bot_service.webdriver_manager, "restore_chrome_window_without_focus"
        ):
            logging.debug("Restaurando janela do Chrome antes de buscar elemento.")
            self.bot_service.webdriver_manager.restore_chrome_window_without_focus()
        try:
            return WebDriverWait(self.driver, timeout).until(
                ec.presence_of_element_located((by, value))
            )
        except TimeoutException:
            logging.warning(f"Elemento '{value}' não encontrado após {timeout}s.")
            self.notify(
                "log",
                f"AVISO: Elemento '{value}' não encontrado após {timeout}s.",
                THEME_COLORS["log_warning"],
            )
            return None

    def notify(self, event_type: str, *args: Any, **kwargs: Any) -> None:
        """
        Método público para notificação, evitando uso direto de métodos protegidos do BotService.
        """
        if hasattr(self.bot_service, "notify"):
            return self.bot_service.notify(event_type, *args, **kwargs)
        raise AttributeError("BotService não possui método público de notificação.")

    def open_chat(self, identifier: str, is_group: bool = False) -> bool:
        """
        Abre uma conversa procurando pelo número ou nome do grupo na caixa de pesquisa,
        e pressionando Enter ao encontrar. Otimizado para rapidez e realismo.
        Corrige o foco indevido na barra de pesquisa após a abertura do chat.
        """
        logging.debug(f"Abrindo chat para '{identifier}' (grupo: {is_group})")
        try:
            search_term = identifier if is_group else self.format_phone_number(identifier)
            if not search_term:
                logging.error("Identificador de contato ou grupo inválido.")
                raise ValueError("Identificador de contato ou grupo inválido.")

            # 1. Garantir que a barra de pesquisa está visível
            search_bar = self._wait_for_element(By.XPATH, Locators.SEARCH_BAR, timeout=10)
            if not search_bar:
                logging.error("Barra de pesquisa não encontrada.")
                self.notify(
                    "log",
                    "Barra de pesquisa não encontrada.",
                    THEME_COLORS["log_error"],
                )
                return False

            # 2. Clica na barra de pesquisa para garantir o foco
            search_bar.click()
            time.sleep(random.uniform(HUMAN_TYPING_DELAY_MIN, HUMAN_TYPING_DELAY_MAX))

            # 3. Limpa campo de busca (Ctrl+A + Delete)
            ActionChains(self.driver).key_down(Keys.CONTROL).send_keys("a").key_up(
                Keys.CONTROL
            ).send_keys(Keys.DELETE).perform()
            time.sleep(random.uniform(HUMAN_TYPING_DELAY_MIN, HUMAN_TYPING_DELAY_MAX))

            # 4. Digita o termo da busca simulando humano
            for char in str(search_term):
                search_bar.send_keys(char)
                time.sleep(random.uniform(HUMAN_TYPING_DELAY_MIN, HUMAN_TYPING_DELAY_MAX))

            time.sleep(random.uniform(0.05, 0.1))  # Espera para o WhatsApp carregar o resultado
            search_bar.send_keys(Keys.ENTER)
            time.sleep(random.uniform(HUMAN_TYPING_DELAY_MIN, HUMAN_TYPING_DELAY_MAX))

            # 5. Verifica se a caixa de mensagem está disponível (confirma chat aberto)
            message_box = self._wait_for_element(By.XPATH, Locators.MESSAGE_INPUT, timeout=5)
            if message_box:
                message_box.click()
                time.sleep(0.05)
                return True
            else:
                logging.error(f"FALHA: Não foi possível carregar a conversa com '{search_term}'.")
                self.notify(
                    "log",
                    f"FALHA: Não foi possível carregar a conversa com '{search_term}'.",
                    THEME_COLORS["log_error"],
                )
                return False

        except Exception as e:
            logging.exception(f"ERRO ao tentar abrir conversa com '{identifier}': {e}")
            self.notify(
                "log",
                f"ERRO ao tentar abrir conversa com '{identifier}': {e}",
                THEME_COLORS["log_error"],
            )
            return False

    def send_text_message(self, message: str) -> bool:
        """
        Envia uma mensagem de texto, suportando múltiplas linhas (\n) com Shift+Enter.
        """
        logging.debug("Enviando mensagem de texto.")
        try:
            message_box = self._wait_for_element(By.XPATH, Locators.MESSAGE_INPUT, timeout=10)
            lines = message.split("\n")
            for idx, line in enumerate(lines):
                for char in line:
                    message_box.send_keys(char)
                    time.sleep(random.uniform(HUMAN_TYPING_DELAY_MIN, HUMAN_TYPING_DELAY_MAX))
                if idx < len(lines) - 1:
                    # Shift+Enter para nova linha
                    message_box.send_keys(Keys.SHIFT, Keys.ENTER)
                    time.sleep(0.03)
            time.sleep(random.uniform(HUMAN_TYPING_DELAY_MIN, HUMAN_TYPING_DELAY_MAX))
            message_box.send_keys(Keys.ENTER)

            logging.info("Mensagem de texto enviada com sucesso.")
            self.notify("log", "Mensagem de texto enviada.", THEME_COLORS["log_success"])
            return True
        except Exception as e:
            logging.exception(f"ERRO ao enviar mensagem de texto: {e}")
            self.notify(
                "log",
                f"ERRO ao enviar mensagem de texto: {e}",
                THEME_COLORS["log_error"],
            )
            return False

    def send_attachment(self, file_path_str: str, is_media: bool) -> bool:
        """Anexa um arquivo, seja como mídia/áudio ou como documento."""
        file_path = Path(file_path_str)
        logging.debug(f"Enviando anexo: {file_path.name} (media: {is_media})")
        try:
            attach_button = self._wait_for_element(By.XPATH, Locators.ATTACHMENT_BUTTON, timeout=10)
            if not attach_button:
                raise NoSuchElementException("Botão de anexo não encontrado.")
            attach_button.click()
            time.sleep(random.uniform(0.1, 0.2))

            input_locator = (
                Locators.ATTACH_IMAGE_VIDEO_INPUT if is_media else Locators.ATTACH_DOCUMENT_INPUT
            )

            # Espera explícita pelo input de anexo aparecer
            attach_input = self._wait_for_element(By.XPATH, input_locator, timeout=5)
            if not attach_input:
                raise NoSuchElementException(f"Input de anexo '{input_locator}' não encontrado.")

            attach_input.send_keys(str(file_path.absolute()))

            # Espera mais longa para o botão de envio, pois o anexo pode demorar para carregar
            send_button = self._wait_for_element(
                By.XPATH, Locators.SEND_ATTACHMENT_BUTTON, timeout=20
            )
            if not send_button:
                raise NoSuchElementException("Botão de envio do anexo não encontrado.")
            send_button.click()

            logging.info(f"Anexo '{file_path.name}' enviado com sucesso.")
            self.notify(
                "log",
                f"Anexo '{file_path.name}' enviado com sucesso.",
                THEME_COLORS["log_success"],
            )
            return True
        except Exception as e:
            logging.exception(f"ERRO ao anexar arquivo '{file_path.name}': {e}")
            self.notify(
                "log",
                f"ERRO ao anexar arquivo '{file_path.name}': {e}",
                THEME_COLORS["log_error"],
            )
            try:
                ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
            except Exception as esc_error:
                logging.warning(f"Falha ao tentar cancelar envio de anexo após erro: {esc_error}")
                self.notify(
                    "log",
                    f"Falha ao tentar cancelar envio de anexo após erro: {esc_error}",
                    THEME_COLORS["log_warning"],
                )
            return False

    def format_phone_number(self, phone: str) -> str:
        """
        Limpa e formata um número de telefone para o padrão internacional (DDI+DDD+Numero),
        mantendo o nono dígito para números de celular brasileiros.
        """
        if not phone:
            logging.warning("Número de telefone vazio ao formatar.")
            return ""

        # Remove tudo que não for dígito
        phone_digits = "".join(re.findall(r"\d+", str(phone)))
        logging.debug(f"Número limpo: {phone_digits}")

        # Se o número já começa com o código do país, assume-se que está correto.
        if phone_digits.startswith(PHONE_COUNTRY_CODE):
            logging.debug("Número já está no padrão internacional.")
            return phone_digits

        # Para números brasileiros (DDD + número), que tipicamente têm 10 (fixo)
        # ou 11 (celular) dígitos.
        if len(phone_digits) in [10, 11]:
            logging.debug("Número brasileiro detectado, aplicando DDI.")
            return f"{PHONE_COUNTRY_CODE}{phone_digits}"

        # Retorna o número limpo para outros casos (pode ser inválido,
        # mas a checagem é feita pelo WhatsApp)
        return phone_digits
