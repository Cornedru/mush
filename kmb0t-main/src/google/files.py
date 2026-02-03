from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import os

from src.google.tools import get_google_token

def find_file_in_folder(filename, folder_id):
    service = build('drive', 'v3', credentials=get_google_token())

    query = (
        f"name = '{filename}' and "
        f"'{folder_id}' in parents and "
        f"trashed = false"
    )

    results = service.files().list(
        q=query,
        corpora="allDrives",
        includeItemsFromAllDrives=True,
        supportsAllDrives=True,
        fields="files(id, name)"
    ).execute()

    files = results.get("files", [])
    return files[0] if files else None


from googleapiclient.http import MediaFileUpload
import os

# Nouvelle version de fichier si déjà existant
def Gdrive_upload_file(
        file_path,
        folder_id,
        mime_type="application/octet-stream"
    ):
    service = build('drive', 'v3', credentials=get_google_token())
    filename = os.path.basename(file_path)

    existing_file = find_file_in_folder(filename, folder_id)

    media = MediaFileUpload(
        file_path,
        mimetype=mime_type,
        resumable=True
    )

    if existing_file:
        # 🔁 Nouvelle version
        file = service.files().update(
            fileId=existing_file["id"],
            media_body=media,
            supportsAllDrives=True,
            fields="id, name, webViewLink"
        ).execute()
    else:
        # 🆕 Nouveau fichier
        file_metadata = {
            "name": filename,
            "parents": [folder_id]
        }

        file = service.files().create(
            body=file_metadata,
            media_body=media,
            supportsAllDrives=True,
            fields="id, name, webViewLink"
        ).execute()

    return file
