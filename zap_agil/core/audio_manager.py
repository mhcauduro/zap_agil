"""
Gerencia gravação, reprodução e descarte de áudio de forma segura,
notificando a UI de forma desacoplada sobre as mudanças de estado.
"""

import threading
import time
from typing import Any

import numpy as np
import sounddevice as sd
import soundfile as sf

from zap_agil.core.constants import (
    AUDIO_CHANNELS,
    AUDIO_DTYPE,
    AUDIO_SAMPLERATE,
    AUDIO_STOP_DELAY,
    AUDIO_THREAD_DELAY,
    THEME_COLORS,
    AudioState,
)
from zap_agil.utils.logging_config import logging


class AudioManager:
    """
    Gerencia operações de áudio (gravação, reprodução, descarte) com segurança de thread.
    """

    def __init__(self, bot_service: Any):
        logging.debug("AudioManager inicializado.")
        self.bot_service = bot_service
        self.is_recording = False
        self.recorded_frames = []
        self._lock = threading.Lock()

        # --- NOVOS ATRIBUTOS PARA CONTROLE DE PLAYBACK ---
        self.playback_thread: threading.Thread | None = None
        self.stream: sd.OutputStream | None = None
        self.stop_playback_event = threading.Event()
        self.pause_playback_event = threading.Event()
        self.pause_playback_event.set()  # Começa "setado" (não pausado)

    def start_recording(self) -> None:
        logging.debug("Iniciando gravação de áudio.")
        # (Este método não muda)
        with self._lock:
            if self.is_recording:
                logging.warning("Tentativa de iniciar gravação enquanto já está gravando.")
                self.bot_service._notify(
                    "log",
                    "A gravação já está em andamento.",
                    THEME_COLORS["log_warning"],
                )
                return
            self.is_recording = True
            self.recorded_frames = []
            self.bot_service._notify("audio_state", AudioState.RECORDING)
            try:
                if not sd.query_devices(kind="input"):
                    logging.error("Nenhum microfone encontrado.")
                    self.bot_service._notify(
                        "log", "Nenhum microfone encontrado.", THEME_COLORS["log_error"]
                    )
                    self.is_recording = False
                    self.bot_service._notify("audio_state", AudioState.IDLE)
                    return
            except Exception as e:
                logging.exception(f"Erro ao acessar dispositivos de áudio: {e}")
                self.bot_service._notify(
                    "log",
                    f"Erro ao acessar dispositivos de áudio: {e}",
                    THEME_COLORS["log_error"],
                )
                self.is_recording = False
                self.bot_service._notify("audio_state", AudioState.IDLE)
                return
            threading.Thread(target=self._record_audio_worker, daemon=True).start()

    def stop_recording(self) -> None:
        logging.debug("Parando gravação de áudio.")
        # (Este método não muda)
        with self._lock:
            if not self.is_recording:
                logging.warning("Tentativa de parar gravação sem gravação ativa.")
                return
            self.is_recording = False
        time.sleep(AUDIO_STOP_DELAY)
        if not self.recorded_frames:
            logging.warning("Nenhuma amostra de áudio foi gravada.")
            self.bot_service._notify("audio_state", AudioState.IDLE)
            return
        try:
            raw_recording = np.concatenate(self.recorded_frames, axis=0)
            sf.write(
                self.bot_service.temp_audio_path,
                raw_recording,
                AUDIO_SAMPLERATE,
                format="OGG",
                subtype="OPUS",
            )
            duration = len(raw_recording) / AUDIO_SAMPLERATE
            logging.debug(f"Áudio gravado com sucesso. Duração: {duration:.2f}s")
            # Áudio gravado com sucesso, log apenas interno
            self.bot_service._notify("audio_state", AudioState.READY, duration=duration)
        except Exception as e:
            logging.exception(f"Falha ao salvar áudio: {e}")
            # Falha ao salvar áudio, log apenas interno
            self.bot_service._notify("audio_state", AudioState.IDLE)

    def play_recorded_audio(self) -> None:
        logging.debug("Solicitada reprodução de áudio gravado.")
        """
        Inicia a reprodução do áudio gravado em uma thread separada.
        """
        if self.playback_thread and self.playback_thread.is_alive():
            logging.warning("Tentativa de reprodução enquanto já está em andamento.")
            return
        if not self.bot_service.temp_audio_path.exists():
            logging.error("Nenhum áudio gravado para reproduzir.")
            return

        self.stop_playback_event.clear()
        self.pause_playback_event.set()

        self.playback_thread = threading.Thread(target=self._play_audio_worker, daemon=True)
        self.playback_thread.start()

    def pause_playback(self):
        logging.debug("Pausando reprodução de áudio.")
        """
        Pausa a reprodução de áudio (mantém o stream aberto, apenas pausa o loop).
        """
        # Sempre tenta pausar o evento, mesmo se não houver stream ativo
        self.pause_playback_event.clear()  # Pausa o loop do worker
        if self.stream and self.stream.active:
            logging.debug("Playback pausado via evento clear.")
        # Sempre notifica a UI para garantir atualização do botão
        self.bot_service._notify("audio_state", AudioState.PAUSED)

    def resume_playback(self):
        logging.debug("Retomando reprodução de áudio.")
        """
        Retoma a reprodução de áudio (continua o loop do worker).
        """
        if self.stream:
            logging.debug("Playback retomado via evento set.")
            self.pause_playback_event.set()  # Apenas retoma o loop
            self.bot_service._notify("audio_state", AudioState.PLAYING)

    def stop_playback(self):
        logging.debug("Parando reprodução de áudio.")
        """
        Para completamente a reprodução e limpa os recursos.
        """
        if self.playback_thread and self.playback_thread.is_alive():
            self.stop_playback_event.set()
            self.pause_playback_event.set()  # Garante que a thread não fique presa na pausa
            # Não notificamos IDLE aqui, a própria thread notifica quando termina

    def discard_recorded_audio(self) -> None:
        logging.debug("Descartando áudio gravado e parando reprodução, se ativa.")
        """
        Descarta o arquivo de áudio e para qualquer reprodução em andamento.
        """
        self.stop_playback()  # Para a reprodução se estiver ativa
        with self._lock:
            self.recorded_frames = []
            if self.bot_service.temp_audio_path.exists():
                try:
                    self.bot_service.temp_audio_path.unlink()
                    logging.info("Arquivo de áudio temporário removido.")
                except OSError as e:
                    logging.exception(f"Falha ao apagar áudio temporário: {e}")
        # A notificação de IDLE é enviada pela thread de playback ao parar,
        # ou aqui se não estava tocando.
        if not (self.playback_thread and self.playback_thread.is_alive()):
            self.bot_service._notify("audio_state", AudioState.IDLE)

    def get_audio_duration(self, file_path: str) -> float:
        logging.debug(f"Obtendo duração do arquivo de áudio: {file_path}")
        # (Este método não muda)
        try:
            with sf.SoundFile(file_path) as f:
                return f.frames / f.samplerate
        except (sf.LibsndfileError, RuntimeError, FileNotFoundError):
            logging.exception("Erro ao obter duração do áudio.")
            return 0.0

    def _record_audio_worker(self) -> None:
        logging.debug("Thread de gravação de áudio iniciada.")
        # (Este método não muda)
        try:
            with sd.InputStream(
                samplerate=AUDIO_SAMPLERATE,
                channels=AUDIO_CHANNELS,
                dtype=AUDIO_DTYPE,
                callback=self._audio_callback,
            ):
                while self.is_recording:
                    time.sleep(AUDIO_THREAD_DELAY)
        except Exception as e:
            logging.exception(f"Erro de microfone: {e}")
            self.is_recording = False
            self.bot_service._notify("audio_state", AudioState.IDLE)

    def _play_audio_worker(self) -> None:
        logging.debug("Thread de reprodução de áudio iniciada.")
        """
        Worker que efetivamente reproduz o áudio usando um stream controlável.
        """
        duration = 0.0
        try:
            with sf.SoundFile(self.bot_service.temp_audio_path) as audio_file:
                duration = audio_file.frames / audio_file.samplerate
                if duration == 0:
                    logging.error("Arquivo de áudio inválido ou com duração zero.")
                    raise ValueError("Arquivo de áudio inválido ou com duração zero.")

                self.stream = sd.OutputStream(
                    samplerate=audio_file.samplerate,
                    channels=audio_file.channels,
                    dtype=AUDIO_DTYPE,
                )
                self.stream.start()

                self.bot_service._notify("audio_state", AudioState.PLAYING, duration=duration)

                chunk_size = 1024
                while not self.stop_playback_event.is_set():
                    logging.debug("Loop de reprodução aguardando evento de pausa/play.")
                    self.pause_playback_event.wait()  # Pausa aqui se o evento for 'clear'
                    logging.debug("Evento liberado, lendo chunk de áudio.")

                    data = audio_file.read(chunk_size, dtype=AUDIO_DTYPE)
                    if len(data) == 0:
                        logging.info("Fim do arquivo de áudio.")
                        break  # Fim do arquivo
                    self.stream.write(data)

        except Exception as e:
            logging.exception(f"Erro ao reproduzir áudio: {e}")
        finally:
            if self.stream:
                self.stream.stop()
                self.stream.close()
                self.stream = None

            # Notifica o estado final
            if self.stop_playback_event.is_set():
                logging.info("Reprodução de áudio parada pelo usuário.")
                self.bot_service._notify("audio_state", AudioState.IDLE)  # Foi parado via descarte
            else:
                logging.info("Reprodução de áudio finalizada normalmente.")
                self.bot_service._notify(
                    "audio_state", AudioState.READY, duration=duration
                )  # Terminou normalmente

    def _audio_callback(self, indata, frames, time_, status) -> None:
        logging.debug("Callback de áudio chamado.")
        # (Este método não muda)
        if status:
            logging.warning(f"Aviso do stream de áudio: {status}")
            self.bot_service._notify("log", f"Aviso do stream de áudio: {status}", "gray")
        self.recorded_frames.append(indata.copy())
