# ⚡ Auto-Paster

**Auto-Paster** is a powerful and lightweight data-pasting automation tool designed to streamline repetitive typing tasks. Whether you're handling massive lists of phone numbers, names, or email addresses, Auto-Paster helps you paste them sequentially with a single global hotkey.

<img width="1457" height="989" alt="Screenshot 2026-04-16 135338" src="https://github.com/user-attachments/assets/c0ade82e-f1bf-4608-aa71-767a99f074ba" />

## ✨ Key Features

- **📂 Multi-Category Support**: Organize your data into **Phone**, **Name**, and **Email** categories.
- **🔍 Smart Auto-Detect**: Optional context-awareness! The tool can attempt to detect the type of field you've clicked on (Email, Phone, etc.) and automatically switch to the correct category.
- **📊 Real-time Stats & Progress**: Visual progress tracking with modern stats cards showing Total, Pasted, and Remaining items.
- **⌨️ Customizable Global Hotkey**: Set your own shortcut (default: `Ctrl+Shift+Space`) to paste the next item from anywhere in Windows.
- **📋 Bulk Add**: Paste hundreds of items at once into the list using the built-in bulk importer.
- **🎨 Premium Dark UI**: A sleek, high-contrast dark theme designed for focus and modern aesthetics.
- **⚙️ Persistent Storage**: Your data and settings are automatically saved locally in `data.json` and `settings.json`.

## 🚀 Getting Started

### Prerequisites

You need Python installed on your Windows machine. Install the required dependencies using pip:

```bash
pip install keyboard pyperclip uiautomation
```

### Running the App

1. Download/Clone this repository.
2. Open your terminal (CMD or PowerShell) as **Administrator** (Required for global keyboard hooks).
3. Run the application:
   ```bash
   python auto_paster.py
   ```

## 🛠️ How to Use

1. **Select a Category**: Choose between Phone, Name, or Email using the pill selector.
2. **Add Data**: Enter items one by one or use the **📋 Bulk** button to paste a list.
3. **Configure Hotkey**: Click the hotkey badge (top right) to record a custom shortcut.
4. **Paste Anywhere**: Click on any input field in any application (browser, excel, etc.) and press your Hotkey. The next unpasted item will be typed instantly!
5. **Auto-Detect**: Toggle "Auto-Detect" to let the app guess the category based on the field you focus.

## 📦 Building Standalone EXE

If you want to create a standalone `.exe` version of this tool:

1. Simply double-click the **`build.bat`** file included in the repository.
2. Or run the following command manually in your terminal:
   ```bash
   pyinstaller --noconsole --onefile --name "auto-paster" auto_paster.py
   ```
3. Find your ready-to-use app in the `dist/` folder.

## 📂 Project Structure

- `auto_paster.py`: The main application source code.
- `build.bat`: One-click build script for Windows.
- `data.json`: Local storage for your pasted items.
- `settings.json`: Configuration for hotkeys and app state.
- `.gitignore`: Configured to keep build artifacts and local data out of your repo.

## 🤝 Contributing

Contributions are welcome! If you have ideas for new features or find any bugs, please open an issue or submit a pull request.

1. Fork the Project.
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`).
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`).
4. Push to the Branch (`git push origin feature/AmazingFeature`).
5. Open a Pull Request.

## 📝 License

Distributed under the MIT License. See `LICENSE` for more information.

---
Made with ❤️ by [Salman Ahamed](https://github.com/Salman-Ahamed)
