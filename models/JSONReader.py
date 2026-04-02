import requests
import base64

class JSONReader:

    def __init__(self, dominio, token=None):
        self.url = "https://sonarcloud.io/api/issues/search?componentKeys=" + dominio + "&types=CODE_SMELL"
        self.token = token
        self.dataJson = None

    def GetReportCodeSmells(self):

        headers = {}

        # Si hay token, agregar autenticacion.
        if self.token:
            auth_value = base64.b64encode(f"{self.token}:".encode("utf-8")).decode("utf-8")
            headers["Authorization"] = f"Basic {auth_value}"

        try:

            response = requests.get(self.url, headers=headers)

            # Repositorio privado sin token o token invalido.
            if response.status_code in (401, 403):
                raise Exception(
                    "The repository is private or the authorization token is invalid. "
                    "Please enable the 'Private repository' option and enter a valid token."
                )

            # Proyecto no encontrado en SonarCloud.
            if response.status_code == 404:
                raise Exception(
                    "Project not found in SonarCloud. "
                    "Verify that the repository name is correct."
                )

            response.raise_for_status()

            self.dataJson = response.json()

            # SonarCloud a veces devuelve 200 con un campo "errors" en el cuerpo
            # cuando el repositorio es privado y no se proporciono token.
            if 'errors' in self.dataJson:
                msg = self.dataJson['errors'][0].get('msg', '').lower()
                if 'not authorized' in msg or 'authorized' in msg or 'authentication' in msg:
                    raise Exception(
                        "The repository is private. "
                        "Please enable the 'Private repository' option and enter a valid token."
                    )
                raise Exception(f"SonarCloud error: {self.dataJson['errors'][0].get('msg', 'Unknown error')}")

        except requests.exceptions.Timeout:
            raise Exception("Connection to SonarCloud timed out.")

        except requests.exceptions.ConnectionError:
            raise Exception("Could not connect to SonarCloud.")

    def extractCodeSmells(self):

        if not self.dataJson or 'issues' not in self.dataJson:
            raise Exception(
                "The repository is private. "
                "Please enable the 'Private repository' option and enter a valid token."
            )

        codeSmellsSonarQube = []

        for issue in self.dataJson['issues']:
            codeSmellsSonarQube.append({
                'rule': issue.get('rule'),
                'line': issue.get('line'),
                'severity': issue.get('severity'),
                'component': issue.get('component').split(':', 1)[-1],
                'issue_key': issue.get('key'),
                'project': issue.get('project'),
                'textRange': issue.get('textRange')
            })
            # print (issue.get('rule'), issue.get('line'), issue.get('severity'), issue.get('component'))

        return codeSmellsSonarQube