#curl -X POST http://helvetia-ai-alb-1572264382.eu-central-1.elb.amazonaws.com/flashcards -d '{"command": "get_sets","content": ""}'
#curl -X POST http://helvetia-ai-alb-1572264382.eu-central-1.elb.amazonaws.com/flashcards -d '{"command": "create_set","content": {"name": "Test Set2", "description": "This is a test set"}}'
#curl -X POST http://helvetia-ai-alb-1572264382.eu-central-1.elb.amazonaws.com/flashcards -d '{"command": "get_sets","content": {"name": "Test Set", "description": "This is a test set"}}' -v
#curl -X POST http://helvetia-ai-alb-1572264382.eu-central-1.elb.amazonaws.com/flashcards -d '{"command": "add_flashcard","content": {"set_name": "kkk", "question": "What is the capital of France2?", "answer": "Paris2"}}' -v
#curl -X POST http://helvetia-ai-alb-1572264382.eu-central-1.elb.amazonaws.com/flashcards -d '{"command": "get_flashcards","content": {"set_name": "kkk"}}' -v
#curl -X POST http://helvetia-ai-alb-1572264382.eu-central-1.elb.amazonaws.com/flashcards -d '{"command": "suggest_flashcard_answer","content": {"question": "What is the capital of France?"}}' -v
curl -X POST http://helvetia-ai-alb-1572264382.eu-central-1.elb.amazonaws.com/flashcards/fileupload \
  -F "file=@text.txt" \
  -v
