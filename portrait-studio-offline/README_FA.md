# Portrait Studio - Windows 11 / Python 3.13

This folder is **source only**. The full offline pack is built using GitHub Actions; the final ZIP includes Python wheels and the BiRefNet Portrait ONNX model.

1. Go to repository **Actions** > **Build Offline Portrait Studio Windows 3.13**.
2. Select **Run workflow**, or use the run automatically triggered by changes to this folder.
3. Download the successful run's artifact: `PortraitStudio_WIN11_PY313_OFFLINE`.
4. Unzip the artifact once, then unzip `PortraitStudio_WIN11_PY313_OFFLINE.zip`.
5. Transfer the ZIP via USB to Windows 11 64-bit with Python 3.13 installed.
6. Extract it, double-click `INSTALL_OFFLINE.cmd`, then `START_STREAMLIT.cmd`.

The model is fetched and MD5-checked in the GitHub Windows runner and placed at `models/birefnet-portrait.onnx`. The app and pip installer do not require Internet after packaging.

Input supports individual images, uploading multiple files, or supplying a local folder path on the machine running Streamlit. Portrait pixels are preserved in the compositing step; segmentation errors are possible at hair and edges. The face-protection mask does not guarantee perfect preservation outside its full-opacity zone.

Approximate download size ~1.1 GB, varies with versions. Pandas is not specified as a direct dependency, though Streamlit may depend on it.
