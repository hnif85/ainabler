import streamlit as st
from groq import Groq
import csv
import os
import pandas as pd

st.set_page_config("Analisa sentimen")

def llm_groq(message, model, assistant="helper",groq_api="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"):
    """message: str, model: str, assistant: str -> str"""
    groq_key1 = "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" 
    client = Groq()

    response = client.chat.completions.create(
        messages=[
            {"role": "system", "content": f"You are great assistant for {assistant} and ready to help user with any occasion. "},
            {"role": "user", "content": message}
        ],
        model=model,
        temperature=0.5,
        max_tokens=4000,
        top_p=1,
        stop=None,
        stream=False,
        api_key=groq_api
    )

    result = response.choices[0].message.content
    return result


def classify_sentiment(sentiment):
    valid_sentiments = ['Positif', 'Netral', 'Negatif']
    if sentiment.strip() in valid_sentiments:
        return sentiment.strip()
    return 'Kosong'

uploaded_file = st.file_uploader("Upload file CSV", type="csv")
analyse = st.button("analisa")



with st.sidebar:
    st.write("Analisis sentimen menggunakan model Open Source running by Groq")
    groq_api = st.text_input("Input kode API Groq")
    llm_options = st.selectbox("Pilih LLM",options=["llama-3.1-70b-versatile", "llama3-8b-8192", "llama-3.3-70b-versatile"]) 
     


if analyse and groq_api :
    # Read CSV file
    df = pd.read_csv(uploaded_file,delimiter=";")
    
    # Create a progress bar
    progress_bar = st.progress(0)
    
    # Create lists to store sentiment and emotion results
    sentiments = []
       
    # Perform sentiment analysis
    #model = "llama-3.1-70b-versatile"
    #model = "llama3-8b-8192"
    model = llm_options
    total_texts = len(df['full_text'])
    allText = df['full_text']

    
    
    for i, text in enumerate(df['full_text'], 1):
        # Update progress bar
        st.write(f"Analisis teks ke-{i} dari {total_texts}")
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
            muatan = llm_groq(prompt, model,groq_api= groq_api)
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

