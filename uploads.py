import tkinter as tk
import pyperclip

def generate_list_item():
    # Read the clipboard content
    clipboard_content = pyperclip.paste().strip()
    
    # Prepare the HTML list items
    if clipboard_content:
        links = clipboard_content.split()  # Split by spaces
        list_items = ""
        
        for link in links:
            link = link.strip()  # Clean up any extra whitespace
            if link:  # Check if the link is not empty
                # Create a formatted string for each link
                list_item = f"""<li class="pdf-item" id="pdf-item">
                    <img src="/files/img/images.png" alt="PDF Logo">
                    <a href="{link}" class="pdf-link"><span id="fileName" class="fileName">{link.split('/')[-1]} - MrGadhvii</span></a>
                    <button class="download-btn"><i class="fas fa-download"></i></button>
                </li>\n\n\n"""  # Three break spaces
                list_items += list_item
        
        # Write to output.txt
        with open('output.txt', 'a') as f:
            f.write(list_items)
        
        # Update the status label
        status_label.config(text="List items generated and saved to output.txt")
    else:
        status_label.config(text="Clipboard is empty!")

# Create the main application window
root = tk.Tk()
root.title("Clipboard to HTML List Item Generator")

# Create and place the Start button
start_button = tk.Button(root, text="Start", command=generate_list_item)
start_button.pack(pady=20)

# Create and place a label to show the status
status_label = tk.Label(root, text="")
status_label.pack(pady=20)

# Run the Tkinter event loop
root.mainloop()