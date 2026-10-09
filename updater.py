import os
import sys
import json
import time
import hashlib
import urllib.request
import urllib.error
import subprocess
import shutil


# ============================================================
# UPDATE CONFIGURATION
# ============================================================

# बाद में यहाँ अपने server की version.json URL डालनी होगी.
# अभी खाली रहने पर updater safely disabled रहेगा.
UPDATE_INFO_URL = "https://raw.githubusercontent.com/megsingh9116/FurnitureProductionSuite/refs/heads/main/version.json"
UPDATER_EXE_NAME = "FurnitureUpdater.exe"
VERSION_FILE_NAME = "version.json"


# ============================================================
# APPLICATION SETTINGS
# ============================================================

APP_NAME = "Furniture Production Suite"

DOWNLOAD_TIMEOUT = 60

TEMP_EXE_NAME = "FurnitureProductionSuite_new.exe"


# ============================================================
# GET APPLICATION DIRECTORY
# ============================================================

def get_app_directory():
    try:
        if getattr(sys, "frozen", False):
            return os.path.dirname(os.path.abspath(sys.executable))

        return os.path.dirname(os.path.abspath(__file__))

    except Exception:
        return os.getcwd()


# ============================================================
# GET MAIN EXE PATH
# ============================================================

def get_main_exe_path():
    app_dir = get_app_directory()

    if getattr(sys, "frozen", False):
        return os.path.join(app_dir, "FurnitureProductionSuite.exe")

    return os.path.join(app_dir, "FurnitureProductionSuite.exe")


# ============================================================
# GET UPDATER EXE PATH
# ============================================================

def get_updater_exe_path():
    app_dir = get_app_directory()
    return os.path.join(app_dir, UPDATER_EXE_NAME)


# ============================================================
# VERSION PARSER
# ============================================================

def parse_version(version):
    try:
        version = str(version).strip()

        parts = version.split(".")

        numbers = []

        for part in parts:
            number = ""

            for char in part:
                if char.isdigit():
                    number += char
                else:
                    break

            if number:
                numbers.append(int(number))
            else:
                numbers.append(0)

        while len(numbers) < 4:
            numbers.append(0)

        return tuple(numbers[:4])

    except Exception:
        return (0, 0, 0, 0)


# ============================================================
# CHECK IF NEW VERSION IS AVAILABLE
# ============================================================

def is_newer_version(current_version, new_version):
    try:
        return parse_version(new_version) > parse_version(current_version)

    except Exception:
        return False


# ============================================================
# SHA256 CALCULATION
# ============================================================

def calculate_sha256(file_path):
    sha256 = hashlib.sha256()

    with open(file_path, "rb") as file:

        while True:
            data = file.read(1024 * 1024)

            if not data:
                break

            sha256.update(data)

    return sha256.hexdigest()


# ============================================================
# DOWNLOAD FILE
# ============================================================

def download_file(url, destination):
    try:

        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": "FurnitureProductionSuite-Updater"
            }
        )

        with urllib.request.urlopen(
            request,
            timeout=DOWNLOAD_TIMEOUT
        ) as response:

            with open(destination, "wb") as file:

                while True:

                    chunk = response.read(1024 * 1024)

                    if not chunk:
                        break

                    file.write(chunk)

        return True

    except Exception:
        return False


# ============================================================
# GET UPDATE INFORMATION
# ============================================================

def get_update_information():
    try:

        if not UPDATE_INFO_URL:
            return None

        request = urllib.request.Request(
            UPDATE_INFO_URL,
            headers={
                "User-Agent": "FurnitureProductionSuite-Updater"
            }
        )

        with urllib.request.urlopen(
            request,
            timeout=DOWNLOAD_TIMEOUT
        ) as response:

            data = response.read().decode("utf-8")

        information = json.loads(data)

        return information

    except Exception:
        return None


# ============================================================
# VALIDATE UPDATE INFORMATION
# ============================================================

def validate_update_information(info):
    try:

        if not isinstance(info, dict):
            return False

        required_fields = [
            "version",
            "url",
            "sha256"
        ]

        for field in required_fields:

            if field not in info:
                return False

            if not str(info[field]).strip():
                return False

        return True

    except Exception:
        return False


# ============================================================
# VERIFY DOWNLOADED EXE
# ============================================================

def verify_downloaded_file(file_path, expected_sha256):

    try:

        if not os.path.exists(file_path):
            return False

        actual_sha256 = calculate_sha256(file_path)

        return (
            actual_sha256.lower()
            == str(expected_sha256).strip().lower()
        )

    except Exception:
        return False


# ============================================================
# START STANDALONE UPDATER
# ============================================================

def start_standalone_updater(
    downloaded_file,
    target_exe,
    new_version
):

    try:

        updater_exe = get_updater_exe_path()

        if not os.path.exists(updater_exe):
            return False

        command = [
            updater_exe,
            "--update",
            downloaded_file,
            target_exe,
            new_version
        ]

        subprocess.Popen(
            command,
            close_fds=True
        )

        return True

    except Exception:
        return False


# ============================================================
# CHECK FOR UPDATE
# ============================================================

def check_for_update(current_version):

    try:

        # ----------------------------------------------------
        # UPDATE SERVER NOT CONFIGURED
        # ----------------------------------------------------

        if not UPDATE_INFO_URL:
            return False

        # ----------------------------------------------------
        # GET UPDATE INFORMATION
        # ----------------------------------------------------

        info = get_update_information()

        if not validate_update_information(info):
            return False

        new_version = str(
            info["version"]
        ).strip()

        download_url = str(
            info["url"]
        ).strip()

        expected_sha256 = str(
            info["sha256"]
        ).strip()

        # ----------------------------------------------------
        # VERSION CHECK
        # ----------------------------------------------------

        if not is_newer_version(
            current_version,
            new_version
        ):
            return False

        # ----------------------------------------------------
        # DOWNLOAD LOCATION
        # ----------------------------------------------------

        app_dir = get_app_directory()

        downloaded_file = os.path.join(
            app_dir,
            TEMP_EXE_NAME
        )

        target_exe = get_main_exe_path()

        # ----------------------------------------------------
        # REMOVE OLD TEMP FILE
        # ----------------------------------------------------

        try:

            if os.path.exists(downloaded_file):
                os.remove(downloaded_file)

        except Exception:
            return False

        # ----------------------------------------------------
        # DOWNLOAD NEW EXE
        # ----------------------------------------------------

        success = download_file(
            download_url,
            downloaded_file
        )

        if not success:
            return False

        # ----------------------------------------------------
        # VERIFY SHA256
        # ----------------------------------------------------

        if not verify_downloaded_file(
            downloaded_file,
            expected_sha256
        ):

            try:
                os.remove(downloaded_file)
            except Exception:
                pass

            return False

        # ----------------------------------------------------
        # START SEPARATE UPDATER
        # ----------------------------------------------------

        started = start_standalone_updater(
            downloaded_file,
            target_exe,
            new_version
        )

        if started:

            return True

        return False

    except Exception:
        return False


# ============================================================
# STANDALONE UPDATE MODE
# ============================================================

def run_standalone_update():

    try:

        if len(sys.argv) < 5:
            return False

        downloaded_file = sys.argv[2]

        target_exe = sys.argv[3]

        new_version = sys.argv[4]

        if not os.path.exists(downloaded_file):
            return False

        if not os.path.exists(target_exe):
            return False

        # ----------------------------------------------------
        # WAIT FOR MAIN APPLICATION TO CLOSE
        # ----------------------------------------------------

        for _ in range(60):

            try:

                with open(
                    target_exe,
                    "ab"
                ):
                    pass

                break

            except Exception:

                time.sleep(1)

        # ----------------------------------------------------
        # BACKUP OLD EXE
        # ----------------------------------------------------

        backup_exe = target_exe + ".backup"

        try:

            if os.path.exists(backup_exe):
                os.remove(backup_exe)

        except Exception:
            pass

        # ----------------------------------------------------
        # CREATE BACKUP
        # ----------------------------------------------------

        try:

            shutil.copy2(
                target_exe,
                backup_exe
            )

        except Exception:
            pass

        # ----------------------------------------------------
        # REPLACE OLD EXE
        # ----------------------------------------------------

        try:

            os.replace(
                downloaded_file,
                target_exe
            )

        except Exception:

            try:

                shutil.copy2(
                    downloaded_file,
                    target_exe
                )

                os.remove(
                    downloaded_file
                )

            except Exception:

                # --------------------------------------------
                # ROLLBACK
                # --------------------------------------------

                try:

                    if os.path.exists(backup_exe):

                        shutil.copy2(
                            backup_exe,
                            target_exe
                        )

                except Exception:
                    pass

                return False

        # ----------------------------------------------------
        # START UPDATED APPLICATION
        # ----------------------------------------------------

        try:

            subprocess.Popen(
                [target_exe],
                close_fds=True
            )

        except Exception:

            # --------------------------------------------
            # ROLLBACK IF NEW EXE DOES NOT START
            # --------------------------------------------

            try:

                if os.path.exists(backup_exe):

                    shutil.copy2(
                        backup_exe,
                        target_exe
                    )

                    subprocess.Popen(
                        [target_exe],
                        close_fds=True
                    )

            except Exception:
                pass

            return False

        # ----------------------------------------------------
        # REMOVE BACKUP
        # ----------------------------------------------------

        try:

            time.sleep(2)

            if os.path.exists(backup_exe):
                os.remove(backup_exe)

        except Exception:
            pass

        return True

    except Exception:
        return False


# ============================================================
# AUTOMATIC STANDALONE MODE
# ============================================================

if __name__ == "__main__":

    try:

        if (
            len(sys.argv) > 1
            and sys.argv[1] == "--update
        ):

            success = run_standalone_update()

            if success:
                sys.exit(0)

            else:
                sys.exit(1)

    except Exception:

        sys.exit(1)