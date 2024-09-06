import os
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
from moviepy.editor import VideoFileClip
import json
from atproto import Client, models

# Carrega variáveis de ambiente
load_dotenv()

# Configurações
twitter_username = os.getenv('TWITTER_USERNAME')
bluesky_handle = os.getenv('BLUESKY_HANDLE')
bluesky_password = os.getenv('BLUESKY_PASSWORD')
nitter_instance = os.getenv('NITTER_INSTANCE')
posted_file = 'posted_tweets.json'

# Autenticando no Bluesky
client = Client()
client.login(bluesky_handle, bluesky_password)

# Cabeçalhos para requisições ao Nitter
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 Edg/128.0.0.0',
}

# Função para carregar tweets já postados
def load_posted_tweets():
    try:
        with open(posted_file, 'r') as f:
            print("Carregando tweets postados.")
            return json.load(f)
    except FileNotFoundError:
        print("Nenhum tweet postado encontrado. Criando nova lista.")
        return []

# Função para salvar tweets postados
def save_posted_tweet(tweet):
    posted_tweets = load_posted_tweets()
    posted_tweets.append(tweet)
    with open(posted_file, 'w') as f:
        json.dump(posted_tweets, f)
    print(f"Tweet postado salvo: {tweet}")

# Função para buscar todos os tweets de uma conta no Nitter
def get_all_tweets(nitter_instance, username):
    page = 1
    tweets = []
    
    while True:
        url = f"{nitter_instance}/{username}/search?f=tweets&p={page}"
        print(f"Obtendo tweets da página {page} de {username}...")
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        tweet_items = soup.find_all('div', class_='timeline-item')
        if not tweet_items:
            break  # Se não encontrar mais tweets, para a busca
        
        for item in tweet_items:
            video = item.find('div', class_='gallery-video')
            image = item.find('div', class_='attachment image')
            caption = item.find('div', class_='tweet-content media-body')
            if video:
                video_url = video.find('source')['src']
                caption_text = caption.text.strip()
                tweets.append((video_url, caption_text))
            elif image:
                image_url = image.find('img')['src']
                caption_text = caption.text.strip()
                tweets.append((image_url, caption_text))
            else:
                text = caption.text.strip()
                tweets.append((None, text))
        
        page += 1  # Vai para a próxima página de tweets
    
    return tweets

# Função para postar tweet no Bluesky
def post_tweet(tweet):
    if tweet:
        if tweet[0] and 'mp4' in tweet[0]:
            video = VideoFileClip(tweet[0])
            client.post_video(video, tweet[1])
            video.close()
        elif tweet[0]:
            client.post_image(tweet[0], tweet[1])
        else:
            client.post_text(tweet[1])
        save_posted_tweet(tweet)
    else:
        print("Nenhum tweet encontrado.")

# Função principal
def main():
    posted_tweets = load_posted_tweets()
    all_tweets = get_all_tweets(nitter_instance, twitter_username)
    
    # Reordenando os tweets do mais antigo para o mais recente
    all_tweets.reverse()
    
    # Postando tweets no Bluesky, do mais antigo para o mais recente
    for tweet in all_tweets:
        if tweet not in posted_tweets:
            post_tweet(tweet)
        else:
            print("Tweet já postado:", tweet)

if __name__ == '__main__':
    main()
