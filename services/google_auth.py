import requests

def verify_google_token(access_token: str):
    res = requests.get(
        "https://www.googleapis.com/oauth2/v3/userinfo",
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    if res.status_code != 200:
        return None

    return res.json()
