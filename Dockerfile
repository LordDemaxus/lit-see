FROM ollama/ollama

RUN ollama serve &
RUN ollama pull mistral:7b-instruct-v0.3-q4_K_M

EXPOSE 11434

FROM python:3.9

RUN wget https://developer.download.nvidia.com/compute/cuda/repos/wsl-ubuntu/x86_64/cuda-wsl-ubuntu.pin
RUN mv cuda-wsl-ubuntu.pin /etc/apt/preferences.d/cuda-repository-pin-600
RUN wget https://developer.download.nvidia.com/compute/cuda/11.7.0/local_installers/cuda-repo-wsl-ubuntu-11-7-local_11.7.0-1_amd64.deb
RUN dpkg -i cuda-repo-wsl-ubuntu-11-7-local_11.7.0-1_amd64.deb
RUN cp /var/cuda-repo-wsl-ubuntu-11-7-local/cuda-*-keyring.gpg /usr/share/keyrings/
RUN apt-get update
RUN apt-get install -y cuda-toolkit-11.7


WORKDIR /app

COPY ./requirements.txt .

RUN pip install --no-cache-dir --upgrade -r requirements.txt

RUN python -m spacy download en_core_web_trf

COPY ./app /app

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
