"""
Chat Session Example - Maintaining conversation context

This example shows how to use ChatSession for multi-turn conversations.
"""

from otk import ChatSession

def main():
    # Create a chat session with a system message
    session = ChatSession(
        model="llama2",
        system_message="You are a helpful AI assistant that provides concise answers.",
        temperature=0.7,
        max_history=20
    )
    
    print("✓ Chat session started")
    print("=" * 50)
    print("Type 'quit' to exit, 'clear' to clear history, 'history' to view history")
    print("=" * 50)
    
    while True:
        # Get user input
        user_input = input("\n👤 You: ").strip()
        
        if not user_input:
            continue
        
        if user_input.lower() == 'quit':
            print("\n👋 Goodbye!")
            break
        
        if user_input.lower() == 'clear':
            session.clear_history()
            print("✓ History cleared!")
            continue
        
        if user_input.lower() == 'history':
            print("\n📜 Conversation History:")
            print("-" * 50)
            for msg in session.get_history():
                role = msg['role'].upper()
                content = msg['content'][:100] + "..." if len(msg['content']) > 100 else msg['content']
                print(f"{role}: {content}")
            print("-" * 50)
            continue
        
        # Send message and get response
        print("\n🤖 Assistant: ", end='', flush=True)
        
        # Stream the response
        response = ""
        for chunk in session.send_stream(user_input):
            print(chunk, end='', flush=True)
            response += chunk
        
        print()  # New line after response


def demo_mode():
    """Run a demo conversation"""
    print("\n🎬 Running demo conversation...\n")
    
    session = ChatSession(
        model="llama2",
        system_message="You are a knowledgeable science teacher.",
        temperature=0.7
    )
    
    questions = [
        "What is photosynthesis?",
        "Why is it important for life on Earth?",
        "Can you give me a simple analogy to understand it better?"
    ]
    
    for question in questions:
        print(f"👤 User: {question}")
        print("🤖 Assistant: ", end='', flush=True)
        
        for chunk in session.send_stream(question):
            print(chunk, end='', flush=True)
        
        print("\n" + "-" * 50)
    
    # Export the conversation
    session.export_history("demo_conversation.json")
    print("\n✓ Conversation saved to demo_conversation.json")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        demo_mode()
    else:
        main()
