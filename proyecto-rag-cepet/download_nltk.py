import nltk
import os
import ssl

try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

# Directorio donde se guardarán los modelos
download_dir = os.path.join(os.getcwd(), 'nltk_data')
os.makedirs(download_dir, exist_ok=True)
print(f"Descargando modelos a: {download_dir}")
nltk.data.path.append(download_dir)
nltk.download('popular', download_dir=download_dir)
print("Descargando 'punkt_tab'...")
nltk.download('punkt_tab', download_dir=download_dir)
print("Descargando 'averaged_perceptron_tagger_eng'...")
nltk.download('averaged_perceptron_tagger_eng', download_dir=download_dir)
print("¡Descarga de modelos NLTK completa!")