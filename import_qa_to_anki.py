from anki.collection import Collection
from anki.notes import Note
import json
import os
import re

def create_model_if_not_exists(col, model_name):
    """Create note type if it doesn't exist"""
    # Check if model exists using all() instead of names()
    if model_name not in [m['name'] for m in col.models.all()]:
        mm = col.models
        model = mm.new(model_name)
        
        # Add fields
        for field_name in ["Question", "Options", "Answer", "Year", "Resource", "Question_No"]:
            field = mm.new_field(field_name)
            mm.add_field(model, field)
        
        # Add cards template
        template = mm.new_template("Card 1")
        template['qfmt'] = """
            <div class="question">{{Question}}</div>
            <br>
            <div class="options">{{Options}}</div>
        """
        template['afmt'] = """
            {{FrontSide}}
            <hr>
            <div class="answer">{{Answer}}</div>
            <br>
            <div class="metadata">
                Year: {{Year}}<br>
                Resource: {{Resource}}<br>
                Question No: {{Question_No}}
            </div>
        """
        model['tmpls'].append(template)
        mm.update(model)
        
        # Set the model as current
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
    
    # Create answers dictionary for easy lookup
    answers_dict = {a.get('q_no'): a.get('answerdetails') for a in answers if 'q_no' in a}
    
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
        
        # Fill note fields
        note['Question'] = q.get('question', '')
        note['Options'] = format_options(q)
        note['Answer'] = answers_dict.get(q['q_no'], '')
        note['Year'] = q.get('year', '')
        note['Resource'] = q.get('resource', '')
        note['Question_No'] = q.get('q_no', '')
        
        # Add note to deck with explicit deck_id
        col.add_note(note, did)  # Changed this line
    
    # Save changes and close collection
    col.save()
    col.close()

if __name__ == "__main__":
    main()