# Flora 🌿

**Flora** is a simple plant explorer and garden management application for the GNOME desktop. It helps you discover new plants, organize your personal garden, track care tasks, and plan your gardening spaces.

Built with **Python**, **GTK 4**, and **Libadwaita**.

## ✨ Features

*   **🔍 Plant Search**: Discover plants using global databases. Supports **Trefle** annd **Perenual** APIs.
*   **🪴 My Plants**: Save your favorite plants to your local library. Add personal notes, track watering history, and customize photos.
*   **🏡 My Gardens**: Organize your plants into collections (e.g., "Indoor Garden", "Raised Bed"). Assign plants to specific gardens to keep track of where everything is growing.
*   **📅 Reminders**: Create tasks and set due dates for watering, fertilizing, or pruning. View tasks in a list or on a calendar.
*   **📖 Journal**: Keep a gardening diary to record your progress, thoughts, and observations.
*   **🌤️ Dashboard**: Get a quick overview of your garden status, upcoming tasks, and weather forecast.


## 🚀 Getting Started

### Prerequisites

*   Python 3.11+
*   GTK 4
*   Libadwaita 1.0+
*   PyGObject

### Installation

**Flatpak (Recommended)**

Flora is designed to be installed via Flatpak.

1.  Ensure you have `flatpak` and `flatpak-builder` installed.
2.  Clone the repository:
    ```bash
    git clone https://github.com/cadmiumcmyk/Flora.git
    cd Flora
    ```
3.  Build and install:
    ```bash
    flatpak-builder --user --install --force-clean build-dir com.github.cadmiumcmyk.Flora.json
    ```
4.  Run:
    ```bash
    flatpak run com.github.cadmiumcmyk.Flora
    ```

**Manual Execution (Development)**

1.  Install system dependencies (e.g., `libadwaita-devel`, `python3-gobject`).
2.  Install Python dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3.  Run the application:
    ```bash
    python3 main.py
    ```

## 🛠️ Configuration

### API Keys
Flora relies on external APIs for plant data. To unlock full search capabilities:
1.  Go to **Settings**.
2.  Select your preferred **API Provider** (Trefle or Perenual).
3.  Enter your **API Key** (obtained from the provider's website).
    *   *Trefle*: Get a token from [trefle.io](https://trefle.io/).
    *   *Perenual*: Get a key from [perenual.com](https://perenual.com/).
    
### Weather
To see local weather on the dashboard:
1.  Go to **Settings**.
2.  Enter your **City Name** in the "Weather Location" field.

## 🏗️ Technical Details

*   **Language**: Python 3
*   **UI Toolkit**: GTK 4 + Libadwaita
*   **Database**: SQLite (`plants.db` in user data dir)
*   **APIs**: 
    *   [Open-Meteo](https://open-meteo.com/) (Weather)
    *   [Trefle](https://trefle.io/) (Plant Data)
    *   [Perenual](https://perenual.com/) (Plant Data)
    

## 📂 Project Structure

*   `main.py`: Entry point.
*   `window.py`: Main window logic and view orchestration.
*   `window.ui`: GTK template definition for the main window.
*   `database.py`: SQLite database manager.
*   `ui/views/`: Modular view controllers.
    *   `dashboard.py`: Home screen logic.
    *   `search.py`: API search logic.
    *   `details.py`: Plant details and editing.
    *   `collections.py`: "My Gardens" list and management.
    *   `reminders.py`: Task management.
    *   `journal.py`: Journal entry management.

## 📄 License

This project is licensed under the GNU General Public License v3.0
