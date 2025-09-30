# Azure Identity 라이브러리에서 인증 자격 증명을 불러오기
# - DefaultAzureCredential: 로컬 az login, Managed Identity 등 자동 선택
from azure.identity import DefaultAzureCredential

# Azure Key Vault의 비밀(Secret)을 읽기 위한 클라이언트 불러오기
from azure.keyvault.secrets import SecretClient

# os 모듈은 Key Vault URL 등 환경변수 가져오는 데 사용
import os


class SecretManager:
    """
    Azure Key Vault에서 비밀(Secret)을 관리하는 클래스
    """

    def __init__(self):
        # Key Vault URL (예: https://<vault-name>.vault.azure.net)
        key_vault_url = os.getenv("KEYVAULT_URL")

        if not key_vault_url:
            raise ValueError("환경변수 KEYVAULT_URL 이 설정되지 않았습니다.")

        # 인증 자격 증명 (az login 또는 Managed Identity 사용)
        credential = DefaultAzureCredential()

        # Key Vault 클라이언트 생성
        self.client = SecretClient(vault_url=key_vault_url, credential=credential)

    def get_secret(self, name: str) -> str:
        """
        Key Vault에서 특정 Secret 값을 가져오는 함수
        :param name: Key Vault에 저장된 Secret 이름
        :return: Secret 값 (문자열)
        """
        secret = self.client.get_secret(name)
        return secret.value
