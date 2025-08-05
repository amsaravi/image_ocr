from anki.collection import Collection
from anki.notes import Note
import json
import os
import re

def create_model_if_not_exists(col, model_name):
    """Create note type if it doesn't exist"""
    if model_name not in [m['name'] for m in col.models.all()]:
        mm = col.models
        model = mm.new(model_name)
        
        # Add fields
        fields = ["Question", "Options", "Answer", "CorrectAnswer", "Year", 
                 "Resource", "Question_No", "Question_File", "Answer_File"]
        for field_name in fields:
            field = mm.new_field(field_name)
            mm.add_field(model, field)
        
        # Add cards template with RTL support
        template = mm.new_template("Card 1")
        template['qfmt'] = """
            <div style="direction: rtl; text-align: right;">
                <div class="question">{{Question}}</div>
                <br>
                <div class="options">{{Options}}</div>
                <br>
                <small>Question File: {{Question_File}}</small>
            </div>
        """
        template['afmt'] = """
            {{FrontSide}}
            <hr>
            <div style="direction: rtl; text-align: right;">
                <div class="correct-answer">پاسخ صحیح: {{CorrectAnswer}}</div>
                <br>
                <div class="answer">{{Answer}}</div>
                <br>
                <div class="metadata">
                    سال: {{Year}}<br>
                    منبع: {{Resource}}<br>
                    شماره سوال: {{Question_No}}<br>
                    فایل پاسخ: {{Answer_File}}
                </div>
            </div>
        """
        model['tmpls'].append(template)
        
        # Add CSS
        model['css'] = """
        .card {
            font-family: Arial, 'Iranian Sans', sans-serif;
            font-size: 16px;
            direction: rtl;
            text-align: right;
        }
        .question {
            font-weight: bold;
        }
        .correct-answer {
            color: green;
            font-weight: bold;
        }
        .metadata {
            font-size: 0.9em;
            color: #666;
        }
        """
        
        mm.update(model)
        col.models.set_current(model)
    
    return col.models.by_name(model_name)

def format_options(q_dict):
    """Format options as HTML list"""
    options = []
    for i in range(1, 5):
        opt_key = f"option{i}"
        if opt_key in q_dict and q_dict[opt_key]:
            options.append(q_dict[opt_key])
    return "<br>".join(options)

def main():
    # Read JSON files
    with open('physiology_Q.json', 'r', encoding='utf-8') as f:
        questions = json.load(f)
    
    with open('physiology_A.json', 'r', encoding='utf-8') as f:
        answers = json.load(f)
    
    # Create answers dictionary
    answers_dict = {str(a.get('AnswerNO')): {
        'answerdetails': a.get('answerdetails', ''),
        'CorrectAnswer': a.get('CorrectAnswer', ''),
        'file_name': a.get('file_name', '')
    } for a in answers if 'AnswerNO' in a}
    
    # Get deck name from file name
    deck_name = os.path.splitext(os.path.basename('physiology_Q.json'))[0]
    
    # Open Anki collection
    col_path = os.path.expanduser("~/.local/share/Anki2/User 1/collection.anki2")
    col = Collection(col_path)
    
    # Create deck if it doesn't exist
    did = col.decks.id(deck_name)
    
    # Create note type if it doesn't exist
    model = create_model_if_not_exists(col, "Q_A_mama")
    
    # Add notes
    for q in questions:
        if 'q_no' not in q:
            continue
            
        note = Note(col, model)
        
        # Get answer data
        answer_data = answers_dict.get(q['q_no'], {})
        "fds".replace(".pdf","")
        # Fill note fields
        note['Question'] = q.get('question', '')
        note['Options'] = format_options(q)
        note['Answer'] = answer_data.get('answerdetails', '')
        note['CorrectAnswer'] = answer_data.get('CorrectAnswer', '')
        note['Year'] = q.get('year', '')
        note['Resource'] = q.get('resource', '')
        note['Question_No'] = q.get('q_no', '')
        note['Question_File'] = f"___{q.get('file_name', '').replace('.jpg','')}____"
        note['Answer_File'] = f"___{answer_data.get('file_name', '').replace('.jpg','')}____"
        
        # Add note to deck with explicit deck_id
        col.add_note(note, did)
    
    # Close collection
    col.close()

if __name__ == "__main__":
    main()