from anki.collection import Collection
from anki.notes import Note
import json
import os
import re
import argparse

def create_model_if_not_exists(col, model_name):
    """Create note type if it doesn't exist"""
    if model_name not in [m['name'] for m in col.models.all()]:
        mm = col.models
        model = mm.new(model_name)
        
        # Add fields
        fields = ["Question", "Answer", "CorrectAnswer", "Question_No", "Image_Name", "Answer_Image", "AI_Opinion"]
        for field_name in fields:
            field = mm.new_field(field_name)
            mm.add_field(model, field)
        
        # Add cards template with RTL support
        template = mm.new_template("Card 1")
        template['qfmt'] = """
            <div style="direction: rtl; text-align: right;">
                <div class="question">{{Question}}</div>
                <br>
                <small>Image Name: {{Image_Name}}</small>
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
                    شماره سوال: {{Question_No}}<br>
                    تصویر پاسخ: {{Answer_Image}}<br>
                    نظر هوش مصنوعی: {{AI_Opinion}}
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

def main():
    parser = argparse.ArgumentParser(description="Import QA data from a JSON file to Anki.")
    parser.add_argument('json_file', type=str, help="Path to the JSON file containing QA data.")
    args = parser.parse_args()

    # Read JSON files
    with open(args.json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Get deck name
    deck_name = "Medical Questions"
    
    # Open Anki collection
    if os.name == 'nt': # Windows
        col_path = os.path.join(os.getenv('APPDATA'), 'Anki2', 'User 1', 'collection.anki2')
    else: # Linux/macOS
        col_path = os.path.expanduser("~/.local/share/Anki2/User 1/collection.anki2")
    col = Collection(col_path)
    
    # Create deck if it doesn't exist
    did = col.decks.id(deck_name)
    
    # Create note type if it doesn't exist
    model = create_model_if_not_exists(col, "Medical Q&A")
    
    # Add notes
    for chapter in data.get('chapters', []):
        chapter_name = chapter.get('chapter_name', 'Unknown Chapter')
        for q in chapter.get('questions', []):
            note = Note(col, model)
            
            # Fill note fields
            note['Question'] = q.get('Q_main', '')
            note['Answer'] = q.get('Answer', '')
            note['CorrectAnswer'] = q.get('correct_answer', '')
            note['Question_No'] = q.get('question_no', '')
            note['Image_Name'] = f"___{q.get('image_name', '').replace('.jpg','').replace('.pdf','')}____"
            note['Answer_Image'] = ", ".join([f"___{img.replace('.jpg','')}____" for img in q.get('answer_image', [])])
            
            ai_opinion = q.get('AI-opinion', {})
            ai_opinion_text = []
            if ai_opinion.get('question'):
                ai_opinion_text.append(f"Question: {ai_opinion['question']}")
            if ai_opinion.get('answer'):
                ai_opinion_text.append(f"Answer: {ai_opinion['answer']}")
            if ai_opinion.get('correct_answer'):
                ai_opinion_text.append(f"Correct Answer: {ai_opinion['correct_answer']}")
            note['AI_Opinion'] = "<br>".join(ai_opinion_text)
            
            # Add note to deck with explicit deck_id
            col.add_note(note, did)
    
    # Close collection
    col.close()

if __name__ == "__main__":
    main()