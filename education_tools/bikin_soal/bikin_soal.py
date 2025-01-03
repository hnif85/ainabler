import streamlit as st
import sqlite3
import pandas as pd
from phi.model.groq import Groq
from phi.model.google import Gemini
from phi.agent import Agent
from phi.tools.googlesearch import GoogleSearch
from datetime import datetime



def init_db():
    """Initialize database with necessary tables"""
    conn = sqlite3.connect('education.db')
    cursor = conn.cursor()
    
    # Create table for generated questions if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS generated_questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT,
            topic TEXT,
            level TEXT,
            kelas INTEGER,
            question TEXT,
            options TEXT,
            answer TEXT,
            explanation TEXT,
            is_used BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()

def connect_db():
    """Establish database connection and return connection object"""
    try:
        conn = sqlite3.connect('education.db')
        return conn
    except sqlite3.Error as e:
        st.error(f"Database connection error: {e}")
        return None
    
def get_unique_chapters():
    """Get unique chapters from soal_ujian table"""
    conn = connect_db()
    if conn is not None:
        try:
            query = "SELECT DISTINCT bab FROM soal_ujian ORDER BY bab"
            df = pd.read_sql_query(query, conn)
            conn.close()
            return df['bab'].tolist()
        except sqlite3.Error as e:
            st.error(f"Error fetching chapters: {e}")
            conn.close()
            return []
    return []

def save_generated_question(subject, topic, level, kelas, question_data):
    """Save generated question to database"""
    conn = connect_db()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO generated_questions 
                (subject, topic, level, kelas, question, options, answer, explanation)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                subject,
                topic,
                level,
                kelas,
                question_data['question'],
                question_data['options'],
                question_data['answer'],
                question_data['explanation']
            ))
            conn.commit()
            conn.close()
            return True
        except sqlite3.Error as e:
            st.error(f"Error saving question: {e}")
            conn.close()
            return False
    return False

def parse_generated_response(response_text):
    """Parse the generated response into structured data"""
    lines = response_text.split('\n')
    result = {
        'question': '',
        'options': '',
        'answer': '',
        'explanation': ''
    }
    
    current_section = None
    for line in lines:
        if line.lower().startswith('soal:'):
            current_section = 'question'
        elif line.lower().startswith('alternatif jawaban:'):
            current_section = 'options'
        elif line.lower().startswith('kunci jawaban:'):
            current_section = 'answer'
        elif line.lower().startswith('pembahasan:'):
            current_section = 'explanation'
        elif current_section and line.strip():
            result[current_section] = result[current_section] + '\n' + line.strip() if result[current_section] else line.strip()
    
    return result

def get_generated_questions(filters=None):
    """Fetch generated questions with optional filters"""
    conn = connect_db()
    if conn is not None:
        try:
            query = "SELECT * FROM generated_questions WHERE 1=1"
            params = []
            
            if filters:
                if filters.get('subject'):
                    query += " AND subject = ?"
                    params.append(filters['subject'])
                if filters.get('topic'):
                    query += " AND topic = ?"
                    params.append(filters['topic'])
                if filters.get('level'):
                    query += " AND level = ?"
                    params.append(filters['level'])
                if filters.get('kelas'):
                    query += " AND kelas = ?"
                    params.append(filters['kelas'])
                if 'is_used' in filters:
                    query += " AND is_used = ?"
                    params.append(filters['is_used'])
            
            query += " ORDER BY created_at DESC"
            df = pd.read_sql_query(query, conn, params=params)
            conn.close()
            return df
        except sqlite3.Error as e:
            st.error(f"Error fetching generated questions: {e}")
            conn.close()
            return pd.DataFrame()
    return pd.DataFrame()

def toggle_question_usage(question_id):
    """Toggle the used status of a question"""
    conn = connect_db()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE generated_questions 
                SET is_used = NOT is_used 
                WHERE id = ?
            """, (question_id,))
            conn.commit()
            conn.close()
            return True
        except sqlite3.Error as e:
            st.error(f"Error updating question status: {e}")
            conn.close()
            return False
    return False

def get_soal_example(bab_name):
    """Fetch questions by chapter and return as pandas DataFrame"""
    conn = connect_db()
    if conn is not None:
        try:
            query = """
                SELECT bab, nomor_soal, pertanyaan, opsi_a, opsi_b 
                FROM soal_ujian 
                WHERE bab = ?
                ORDER BY nomor_soal
            """
            df = pd.read_sql_query(query, conn, params=(bab_name,))
            conn.close()
            return df
        except sqlite3.Error as e:
            st.error(f"Error fetching data: {e}")
            conn.close()
            return pd.DataFrame()
    return pd.DataFrame()

def bikin_soal(mapel, tingkat, contoh_soal, material):
    """Generate multiple questions based on subject and level"""
    prompt_soal = f"""buatkan 1 soal, alternatif jawaban dan pembahasan untuk {mapel} pada level {tingkat} dengan material {material} 
                    dengan contoh soal seperti salah satu dari contoh soal berikut ({contoh_soal})
                    format hasil untuk setiap soal adalah sebagai berikut :
                    Soal:
                    alternatif jawaban:
                    kunci jawaban:
                    pembahasan:
                    """ 
    
    create_soal = Agent(
        name="Create soal",
        description="Create soal based on subject and level",
        model=Gemini(
            id="gemini-2.0-flash-exp",
            api_key=("AIzaSyB-DJi1VqfUYvK2ml5bJ5C9UDrtoFL4a58")
        ),
        tools=[GoogleSearch(
            fixed_max_results=5)],
    )

    soal = create_soal.run(prompt_soal)
    return soal.content

def parse_multiple_questions(response_text):
    """Parse multiple questions from the generated response"""
    questions = response_text.split('###')
    parsed_questions = []
    
    for question in questions:
        if question.strip():
            parsed_question = parse_generated_response(question)
            if all(parsed_question.values()):  # Check if all fields are non-empty
                parsed_questions.append(parsed_question)
    
    return parsed_questions

def main():
    st.set_page_config(page_title="Question Bank", page_icon="📚", layout="wide")
    
    # Initialize database
    init_db()
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs(["Generate Questions", "View Questions","Unduh soal"])
    
    with tab1:
        st.title("Generate New Questions")
        
        # Filters for question generation
        col1, col2, col3,col4,col5 = st.columns(5)
        with col1:
            mapel = st.selectbox("Subject", ["Mathematics", "Physics", "Chemistry"])
        with col2:
            bab_pilihan = st.selectbox("Topic", get_unique_chapters())
        with col3:
            tingkat = st.selectbox("Level", ["Basic", "Intermediate", "Advanced"])
        with col4:
            number_soal = st.number_input("berapa soal yang ingin di buat: ",min_value=1, max_value=10, value=1)
        with col5:
            kelas = st.number_input("ini untuk kelas berapa?",min_value=7, max_value=12, value=12)
        
        if st.button("Generate Questions"):
           for number in range(number_soal):
                with st.spinner(f"Generating question {number + 1} of {number_soal}"):
                    hasil = bikin_soal(mapel, tingkat, "", bab_pilihan)
                    parsed_result = parse_generated_response(hasil)
                    
                    if save_generated_question(mapel, bab_pilihan, tingkat, kelas, parsed_result):
                        st.success(f"Question {number + 1} generated and saved successfully!")
                        st.markdown(hasil)
                    else:
                        st.error(f"Failed to save question {number + 1}.")
            
    
    with tab2:
        st.title("Question Bank")
        
        # Filters for viewing questions
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            subject_filter = st.selectbox("Filter by Subject", ["All"] + ["Mathematics", "Physics", "Chemistry"])
        with col2:
            topic_filter = st.selectbox("Filter by Topic", ["All"] + get_unique_chapters())
        with col3:
            level_filter = st.selectbox("Filter by Level", ["All"] + ["Basic", "Intermediate", "Advanced"])
        with col4:
            usage_filter = st.selectbox("Filter by Usage", ["All", "Used", "Unused"])
        with col5:
            kelas_filter = st.selectbox("Filter by Kelas", ["All", "7","8","9","10","11","12"])
            
        
        # Prepare filters
        filters = {}
        if subject_filter != "All":
            filters['subject'] = subject_filter
        if topic_filter != "All":
            filters['topic'] = topic_filter
        if level_filter != "All":
            filters['level'] = level_filter
        if usage_filter != "All":
            filters['is_used'] = (usage_filter == "Used")
        if level_filter != "All":
            filters['kelas'] = kelas_filter
        
        # Fetch and display questions
        questions_df = get_generated_questions(filters)
        if not questions_df.empty:
            for idx, row in questions_df.iterrows():
                with st.expander(f"Question {idx + 1} - {row['subject']} ({row['topic']} ) kelas {row['kelas']}"):
                    st.write("Question:", row['question'])
                    st.write("Options:", row['options'])
                    st.write("Answer:", row['answer'])
                    st.write("Kelas:", str(row['kelas']))
                    st.write("Explanation:", row['explanation'])
                    
                    # Toggle usage status
                    current_status = "Used" if row['is_used'] else "Unused"
                    if st.button(f"Mark as {'Unused' if row['is_used'] else 'Used'}", key=f"toggle_{row['id']}"):
                        if toggle_question_usage(row['id']):
                            st.rerun()
                    
                    st.write(f"Status: {current_status}")
                    st.write(f"Created: {row['created_at']}")
        else:
            st.info("No questions found matching the selected filters.")

    with tab3:
        st.title("Unduh soal")

        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            subject1_filter = st.selectbox("Filter by Subject", ["All"] + ["Mathematics", "Physics", "Chemistry"],key="subject tab 3")
        with col2:
            topic1_filter = st.selectbox("Filter by Topic", ["All"] + get_unique_chapters(),key="topic tab 3")
        with col3:
            level1_filter = st.selectbox("Filter by Level", ["All"] + ["Basic", "Intermediate", "Advanced"],key="level tab 3")
        with col4:
            usage1_filter = st.selectbox("Filter by Usage", ["All", "Used", "Unused"],key="usage tab 3")
        with col5:
            kelas1_filter = st.selectbox("Filter by Kelas", ["All", "7","8","9","10","11","12"],key="kelas tab 3")
            
        
        # Prepare filters
        filters = {}
        if subject_filter != "All":
            filters['subject'] = subject1_filter
        if topic_filter != "All":
            filters['topic'] = topic1_filter
        if level_filter != "All":
            filters['level'] = level1_filter
        if usage_filter != "All":
            filters['is_used'] = (usage1_filter == "Used")
        if level_filter != "All":
            filters['kelas'] = kelas1_filter
        
        # Fetch and display questions
        questions_df = get_generated_questions(filters)

        # Filter kolom yang ingin ditampilkan
        questions_df = questions_df[['question', 'options', 'answer', 'explanation', 'is_used']]

        # Rename columns sesuai kebutuhan
        questions_df.rename(columns={
            'question': 'Question',
            'options': 'Options',
            'answer': 'Answer',
            'explanation': 'Pembahasan',
            'is_used': 'Digunakan'
        }, inplace=True)

        # Transformasi nilai di kolom 'Digunakan'
        questions_df['Digunakan'] = questions_df['Digunakan'].apply(lambda x: 'Dipergunakan' if x else 'Tidak Dipergunakan')

        # Tampilkan dataframe dengan Streamlit
        st.dataframe(questions_df)
if __name__ == "__main__":
    main()