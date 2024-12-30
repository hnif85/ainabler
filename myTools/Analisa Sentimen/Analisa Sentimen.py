import streamlit as st
from groq import Groq
import csv
import os
from home import llm_groq
import pandas as pd

st.set_page_config("Analisa sentimen")

def classify_sentiment(sentiment):
    valid_sentiments = ['Positif', 'Netral', 'Negatif']
    if sentiment.strip() in valid_sentiments:
        return sentiment.strip()
    return 'Kosong'

uploaded_file = st.file_uploader("Upload file CSV", type="csv")
analyse = st.button("analisa")


if analyse:
    # Read CSV file
    df = pd.read_csv(uploaded_file,delimiter=";")
    
    # Create a progress bar
    progress_bar = st.progress(0)
    
    # Create lists to store sentiment and emotion results
    sentiments = []
       
    # Perform sentiment analysis
    #model = "llama-3.1-70b-versatile"
    #model = "llama3-8b-8192"
    model = "llama-3.3-70b-versatile"
    total_texts = len(df['full_text'])
    allText = df['full_text']

    
    
    for i, text in enumerate(df['full_text'], 1):
        # Update progress bar
        progress_bar.progress(i / total_texts)
        
        # Perform sentiment analysis with error handling
        try:
            # Sentiment Analysis
            prompt = f"""Analisis teks berikut dan tentukan apakah kalimat tersebut bermuatan positif, netral, atau negatif. Berikan jawaban yang sesuai hanya dengan salah satu kata tersebut (Positif, Netral, atau Negatif). Jangan menambahkan kata lain selain tiga opsi tersebut. Jika Anda tidak dapat menentukan sentimen, jawab dengan Netral.

                    Contoh
                    Teks: Banyak akun kloning seolah2 pendukung #agussilvy mulai menyerang paslon #aniessandi dengan opini dan argumen pembenaran..jangan terkecoh.
                    Output: Negatif
                    Teks: #agussilvy bicara apa kasihan yaa...lap itu air matanya wkwkwkwk.
                    Output: Negatif
                    Teks: Kalau aku sih gak nunggu hasil akhir QC tp lagi nunggu motif cuitan pak @SBYudhoyono kayak apa.. pasca #AgusSilvy Nyungsep.
                    Output: Negatif
                    Teks: Setia pada #AHY sebab politik Indonesia perlu ada regenerasi yg MATANG agar jgn ada lagi kutu loncat.
                    Output: Positif
                    Teks: @bank_dki ikut2an #moneypolitic untuk kemenangan #ahokdjarot ?? <See-No-Evil Monkey> @ojkindonesia.
                    Output: Negatif
                    Tugas Anda
                    Tentukan sentimen dari teks berikut:
                    {text}

                    Jawaban Anda: [Positif/Negatif]
                    """
            muatan = llm_groq(prompt, model)
            sentiments.append(classify_sentiment(muatan))

            # Emotion Analysis
            #emotion_prompt = f"klasifikasikan muatan emosi yang terkandung dalam kalimat {text} sebagai salah satu diantara ini: Kemarahan, Kebencian, Netral, Kepuasan, Kebahagiaan. hanya tulis muatan emosinya saja tanpa kata kata lain"
            #emotion = llm_groq(emotion_prompt, model)
            #emotions.append(classify_emotion(emotion))
        
        except Exception as e:
            st.error(f"Error processing text {i}: {e}")
            sentiments.append('Netral')
           
    
    # Complete progress bar
    progress_bar.progress(1.0)
    
    # Add sentiment and emotion columns to DataFrame
    df['sentiment'] = sentiments
   
    
    # Save results to a new CSV file with semicolon delimiter
    output_file = f'sentiment_analysis_results6.csv'
    df.to_csv(output_file, index=False, sep=';')
    st.info("file telah disimpan")

