# Smart Office Management System

A comprehensive office management system with camera monitoring, employee tracking, and zone management capabilities.

## Features

- **Camera Management**: Add, configure, and monitor IP cameras
- **Motion Detection**: Automatically detect and record motion events
- **Person Detection**: Identify people in camera feeds
- **Zone Monitoring**: Define and monitor specific areas
- **Employee Management**: Track employees, departments, and positions

## Technology Stack

- **Backend**: Django, Django REST Framework
- **Frontend**: HTML, CSS, JavaScript, Bootstrap
- **Database**: SQLite (development), PostgreSQL (production-ready)
- **Computer Vision**: OpenCV

## Getting Started

### Prerequisites

- Python 3.8+
- pip
- Virtual environment (recommended)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/Karthik0704/Office_managment_system.git
   cd Office_managment_system
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run migrations:
   ```bash
   python manage.py migrate
   ```

5. Create a superuser:
   ```bash
   python manage.py createsuperuser
   ```

6. Start the development server:
   ```bash
   python manage.py runserver
   ```

7. Access the application at http://127.0.0.1:8000/

## Project Structure

- `core/`: Django project settings
- `monitoring/`: Camera monitoring and motion detection
- `employees/`: Employee management and attendance tracking

## API Endpoints

- `/api/monitoring/cameras/`: Camera management
- `/api/monitoring/viewer/`: Camera viewer interface
- `/api/monitoring/motion-events/`: Motion event tracking
- `/api/monitoring/zones/`: Zone management
- `/api/employees/`: Employee management

## Current Functionality

The system currently allows:

1. **Camera Management**
   - Add, edit, and delete cameras through the admin interface
   - View all cameras in the camera viewer interface
   - Start and stop camera streams
   - View real-time camera feeds

2. **Motion Detection**
   - Automatic detection of motion in camera feeds
   - Recording of motion events with snapshots
   - Review of motion events in the admin interface

3. **Basic Employee Management**
   - Management of departments, positions, and employees
   - Basic attendance tracking

## Future Development

- Face recognition for employee identification
- Advanced zone monitoring with entry/exit detection
- Automated attendance system
- Real-time notifications
- Mobile application
- Analytics and reporting dashboard

## License

This project is licensed under the MIT License.
```



