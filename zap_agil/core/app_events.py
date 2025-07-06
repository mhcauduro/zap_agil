"""
Define eventos personalizados para comunicação entre a interface gráfica (UI)
e a lógica de backend (core) do Zap Ágil.
"""

import wx

from .constants import AudioState, CampaignState, ConnectionState

# --- Tipos de Eventos ---
# Criamos um tipo de evento único para cada evento personalizado.
# Isso garante que a UI possa vincular cada tipo a uma função de tratamento específica.

LogEventType = wx.NewEventType()
StatusUpdateEventType = wx.NewEventType()
ProgressUpdateEventType = wx.NewEventType()
ConnectionStatusEventType = wx.NewEventType()
CampaignStatusEventType = wx.NewEventType()
AudioStateEventType = wx.NewEventType()

# --- Binders de Eventos ---
# Binders facilitam a associação (Bind) dos eventos na UI
# (ex: self.Bind(EVT_LOG, self.on_log_event))

EVT_LOG = wx.PyEventBinder(LogEventType, 1)
EVT_STATUS_UPDATE = wx.PyEventBinder(StatusUpdateEventType, 1)
EVT_PROGRESS_UPDATE = wx.PyEventBinder(ProgressUpdateEventType, 1)
EVT_CONNECTION_STATUS = wx.PyEventBinder(ConnectionStatusEventType, 1)
EVT_CAMPAIGN_STATUS = wx.PyEventBinder(CampaignStatusEventType, 1)
EVT_AUDIO_STATE = wx.PyEventBinder(AudioStateEventType, 1)


# --- Classes de Eventos ---
# Cada classe carrega os dados específicos necessários para aquele evento.


class LogEvent(wx.PyEvent):
    """
    Evento para enviar uma mensagem de log para a UI.
    """

    def __init__(self, message: str, color_hex: str):
        super().__init__(eventType=LogEventType)
        self.message = message
        self.color_hex = color_hex


class StatusUpdateEvent(wx.PyEvent):
    """
    Evento para atualizar o texto na barra de status principal.
    """

    def __init__(self, text: str):
        super().__init__(eventType=StatusUpdateEventType)
        self.text = text


class ProgressUpdateEvent(wx.PyEvent):
    """
    Evento para atualizar a barra de progresso da campanha.
    """

    def __init__(self, value: int, max_value: int, message: str = ""):
        super().__init__(eventType=ProgressUpdateEventType)
        self.value = value
        self.max_value = max_value
        self.message = message


class ConnectionStatusEvent(wx.PyEvent):
    """
    Evento que notifica a UI sobre mudanças no estado da conexão.
    """

    # --- CORREÇÃO: Usar o Enum específico em vez de 'Any' ---
    def __init__(self, status: ConnectionState):
        super().__init__(eventType=ConnectionStatusEventType)
        self.status = status


class CampaignStatusEvent(wx.PyEvent):
    """
    Evento que notifica a UI sobre mudanças no estado da campanha.
    """

    # --- CORREÇÃO: Usar o Enum específico em vez de 'Any' ---
    def __init__(self, status: CampaignState):
        super().__init__(eventType=CampaignStatusEventType)
        self.status = status


class AudioStateEvent(wx.PyEvent):
    """
    Evento que notifica a UI sobre mudanças no estado de gravação/reprodução de áudio.
    """

    # --- CORREÇÃO: Usar o Enum específico em vez de 'Any' ---
    def __init__(self, state: AudioState, duration: float = 0.0):
        super().__init__(eventType=AudioStateEventType)
        self.state = state
        self.duration = duration
