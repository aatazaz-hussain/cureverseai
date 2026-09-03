import httpx


class EnsemblSequenceClient:
    BASE_URL = "https://rest.ensembl.org"

    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout

    def get_protein_sequence(self, transcript_id: str) -> str:
        transcript_id = transcript_id.split(".")[0]

        url = f"{self.BASE_URL}/sequence/id/{transcript_id}"

        response = httpx.get(
            url,
            params={
                "type": "protein",
            },
            headers={
                "Content-Type": "text/plain",
            },
            timeout=self.timeout,
        )

        response.raise_for_status()

        sequence = response.text.strip()

        if not sequence:
            raise ValueError(
                f"No protein sequence returned for {transcript_id}"
            )

        return sequence
