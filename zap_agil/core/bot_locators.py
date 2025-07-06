"""
ZAP ÁGIL - ARQUIVO CENTRAL DE LOCALIZADORES (SELETORES)
Contém seletores e XPaths para interação com a interface do WhatsApp Web.
Estes seletores podem mudar com as atualizações do WhatsApp,
então este é o primeiro arquivo a corrigir quando o bot quebra.
"""


class WhatsAppLocators:
    """
    Seletores e XPaths para elementos da interface do WhatsApp Web.
    """

    # Apenas seletores realmente utilizados pelos managers
    QR_CODE_CONTAINER = '//canvas[@aria-label="Scan this QR code to link a device!"]'
    SEARCH_BAR = '//div[@role="textbox" and @contenteditable="true"]'
    MESSAGE_INPUT = (
        '//div[@role="textbox" and @aria-label="Digite uma mensagem" and @contenteditable="true"]'
    )
    ATTACHMENT_BUTTON = '//button[@title="Anexar" and @data-tab="10"] | //div[@title="Anexar"]'
    ATTACH_IMAGE_VIDEO_INPUT = (
        "//span[@data-icon='media-filled-refreshed']/ancestor::li//input[@type='file']"
    )
    ATTACH_DOCUMENT_INPUT = (
        "//span[@data-icon='document-filled-refreshed']/ancestor::li//input[@type='file']"
    )
    SEND_ATTACHMENT_BUTTON = (
        "//div[@role='button' and @aria-label='Enviar'][.//span[@data-icon='wds-ic-send-filled']]"
    )
