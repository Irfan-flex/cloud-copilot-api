Copyright Flexday Solutions LLC, Inc - All Rights Reserved
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
See file LICENSE.txt for full license details.

# Speciphic™ Ask NLP API

This Application consists of NLP APIs for Speciphic™ Ask
The models are a dynamic feature here and can be uploaded by the user

To call the api, you will need to authenticate yourself with a client-credential token as per your configuration

## How to run this application:

Make sure you are in the root directory of the project.
The app runs on **Python 3.11.0**.

### Prepare env

```shell
python -m venv venv
```
OR

```shell
py -3.11 -m pip install virtualenv
py -3.11 -m virtualenv venv
```


### Activate the virtual environment

On Unix or MacOS, using the bash shell

```shell
source venv/bin/activate
```

On Unix or MacOS, using the csh shell

```shell
source venv/bin/activate.csh
```

On Unix or MacOS, using the fish shell

```shell
source venv/bin/activate.fish
```

On Windows using the Command Prompt

```shell
source venv/Scripts/activate
```

On Windows using PowerShell

```shell
source venv\Scripts\Activate.ps1
```

### Install necessary libraries

```shell
pip install -r requirements.txt
```

### Run the API

```shell
python application.py
```

### Installing PDFToTextConverter

install the xpdf binaries if they're not already available on your system.
Make sure that the pdftotext command is available in your terminal after the installation. If xpdf is not installed correctly, you will see errors like:

```
pdftotext is not installed. It is part of xpdf or poppler-utils software suite.
```

#### PDFToTextConverter using fitz for OCR support

To enable OCR support via PDFToTextConverter, you need to install Tesseract:

Windows: `choco install tesseract-ocr`

Linux (Ubuntu): `sudo apt-get install tesseract-ocr`

Mac: `brew install tesseract`

After that, you need to set the environment variable TESSDATA_PREFIX to the path of your Tesseract data directory. Typically this is:

Windows: C:\\Program Files\\Tesseract-OCR\\tessdata

Linux (Ubuntu): /usr/share/tesseract-ocr/4.00/tessdata

Mac (Intel):  /usr/local/Cellar/tesseract/5.3.0_1/share/tessdata

Mac (M1/M2): /opt/homebrew/Cellar/tesseract/5.3.0_1/share/tessdata

### startup.sh not found
If azure throws a startup.sh not found, it means there is some issue with the line ending in startup.sh

to fix run this command in any linux environment and commit this change to git.

`
sed -i -e 's/\r$//' ./startup.sh
`
