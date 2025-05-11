import base64
import io
import logging
import os
import tempfile
from typing import Optional

import pytesseract
from PIL import Image
from pypdf import PdfReader

logger = logging.getLogger(__name__)


class FileDecoder:
    """
    Serviço para decodificar conteúdo de arquivos em Base64 e extrair texto.

    Este serviço suporta diferentes formatos de arquivos, como PDFs e imagens,
    e aplica técnicas apropriadas para extrair o conteúdo textual.
    """

    def __init__(self, tesseract_path: Optional[str] = None):
        """
        Inicializa o decodificador de arquivos.

        Args:
            tesseract_path: Caminho para o executável do Tesseract OCR (opcional)
        """
        # Configura o caminho do Tesseract se fornecido
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path

    def decode_and_extract_text(self, file_content_base64: str, content_type: str) -> str:
        """
        Decodifica o conteúdo em Base64 e extrai o texto.

        Args:
            file_content_base64: Conteúdo do arquivo em Base64
            content_type: Tipo MIME do conteúdo (ex: application/pdf)

        Returns:
            Texto extraído do arquivo

        Raises:
            ValueError: Se o tipo de arquivo não for suportado
        """
        try:
            file_content = base64.b64decode(file_content_base64)

            if content_type == "application/pdf":
                return self._extract_text_from_pdf(file_content)

            elif content_type.startswith("image/"):
                return self._extract_text_from_image(file_content)

            elif content_type == "text/plain":
                return file_content.decode("utf-8")

            elif content_type == "text/csv":
                return file_content.decode("utf-8")

            else:
                raise ValueError(f"Tipo de conteúdo não suportado: {content_type}")

        except Exception as e:
            logger.error(f"Erro ao decodificar arquivo: {str(e)}")
            raise

    def _extract_text_from_pdf(self, pdf_content: bytes) -> str:
        """
        Extrai texto de um arquivo PDF.

        Args:
            pdf_content: Conteúdo do arquivo PDF em bytes

        Returns:
            Texto extraído do PDF
        """
        text = ""

        try:
            pdf = PdfReader(io.BytesIO(pdf_content))

            for page in pdf.pages:
                page_text = page.extract_text() or ""
                text += page_text + "#page\n\npage#"

            # Se não conseguiu extrair texto, pode ser um PDF escaneado, tenta OCR
            if not text.strip():
                return self._extract_text_from_pdf_with_ocr(pdf_content)

            return text

        except Exception as e:
            logger.error(f"Erro ao extrair texto do PDF: {str(e)}")
            # Tenta OCR como fallback
            return self._extract_text_from_pdf_with_ocr(pdf_content)

    def _extract_text_from_pdf_with_ocr(self, pdf_content: bytes) -> str:
        """
        Extrai texto de um PDF usando OCR (para PDFs escaneados).

        Args:
            pdf_content: Conteúdo do arquivo PDF em bytes

        Returns:
            Texto extraído usando OCR
        """
        all_text = ""

        try:
            # Salvar o PDF em um arquivo temporário
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_pdf:
                temp_pdf.write(pdf_content)
                temp_pdf_path = temp_pdf.name

            try:
                # Cria um diretório temporário para as imagens
                temp_dir = tempfile.mkdtemp()

                # Converte PDF para imagens usando ImageMagick
                # pdftoppm é alternativa: pdftoppm -png {temp_pdf_path} {os.path.join(temp_dir, "page")}
                cmd = f"convert -density 300 {temp_pdf_path} {os.path.join(temp_dir, 'page-%03d.png')}"
                os.system(cmd)

                # Processa cada imagem com OCR
                for filename in sorted(os.listdir(temp_dir)):
                    if filename.endswith(".png"):
                        img_path = os.path.join(temp_dir, filename)
                        try:
                            text = pytesseract.image_to_string(Image.open(img_path), lang='por')
                            all_text += text + "\n\n"
                        except Exception as e:
                            logger.error(f"Erro OCR na imagem {filename}: {str(e)}")

                return all_text

            finally:
                # Limpa arquivos temporários
                if os.path.exists(temp_pdf_path):
                    os.unlink(temp_pdf_path)

                # Remove o diretório temporário e seu conteúdo
                import shutil
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)

        except Exception as e:
            logger.error(f"Erro ao extrair texto do PDF com OCR: {str(e)}")
            return ""

    def _extract_text_from_image(self, image_content: bytes) -> str:
        """
        Extrai texto de uma imagem usando OCR.

        Args:
            image_content: Conteúdo da imagem em bytes

        Returns:
            Texto extraído da imagem
        """
        try:
            # Carrega a imagem do conteúdo em bytes
            image = Image.open(io.BytesIO(image_content))

            # Aplica OCR na imagem
            text = pytesseract.image_to_string(image, lang='por')

            return text

        except Exception as e:
            logger.error(f"Erro ao extrair texto da imagem: {str(e)}")
            return ""

