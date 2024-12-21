# PDF Processing Application

This application provides PDF processing capabilities using FastAPI and OpenAI integration. Follow the instructions below to set up and deploy the application on an AWS EC2 instance.

## Server Setup Instructions

### Prerequisites
- AWS Account with EC2 access
- OpenAI API key
- Basic knowledge of Linux commands
- Git installed locally

### AWS EC2 Instance Setup
1. Log into AWS Console and navigate to EC2 Dashboard
2. Launch a new instance with the following specifications:
   - Ubuntu Server 20.04 LTS
   - t2.micro instance type (free-tier eligible)
   - 20GB storage
   - Configure Security Group to allow:
     - Port 22 (SSH)
     - Port 80 (HTTP)
     - Port 443 (HTTPS)
     - Port 8000 (FastAPI)

### Instance Connection
1. Download the .pem key file from AWS
2. Set correct permissions for the key file:
   ```bash
   chmod 400 the-key.pem
   ```
3. Connect to the instance:
   ```bash
   ssh -i the-key.pem ubuntu@<ec2-public-dns>
   ```

### System Setup
1. Update system packages:
   ```bash
   sudo apt update
   sudo apt upgrade -y
   sudo apt install python3-pip python3-venv git -y
   ```

2. Create and setup application directory:
   ```bash
   mkdir app
   cd app
   python3 -m venv venv
   source venv/bin/activate
   git clone https://github.com/ThanhT5/Parser.git
   pip install -r requirements.txt
   ```

3. Configure environment variables:
   - Create a .env file in the project directory
   - Add required variables (e.g., OPENAI_API_KEY)

### Deployment Setup
1. Create a systemd service file:
   ```bash
   sudo nano /etc/systemd/system/pdfapp.service
   ```

2. Add the following configuration:
   ```ini
   [Unit]
   Description=PDF Processing Application
   After=network.target

   [Service]
   User=ubuntu
   WorkingDirectory=/home/ubuntu/app
   Environment="PATH=/home/ubuntu/app/venv/bin"
   Environment="OPENAI_API_KEY=api_key"
   ExecStart=/home/ubuntu/app/venv/bin/uvicorn question_server:app --host 0.0.0.0 --port 8000

   [Install]
   WantedBy=multi-user.target
   ```

3. Start and enable the service:
   ```bash
   sudo systemctl start pdfapp
   sudo systemctl enable pdfapp
   ```

### Usage
- Update your application's HTTP request URL to point to your EC2 instance's public DNS or IP address
- The API will be available at: `http://<ec2-public-dns>:8000`

## Development References

The following resources were utilized in the development of the server infrastructure:

- [Amazon Web Services EC2 Documentation](https://docs.aws.amazon.com/ec2/)
- [Python contextlib Documentation](https://docs.python.org/3/library/contextlib.html#contextlib.contextmanager)
- [OpenAI API Documentation](https://platform.openai.com/docs)
- [OpenAI Tiktoken](https://github.com/openai/tiktoken)
- [PDFPlumber](https://github.com/jsvine/pdfplumber)
- [psutil](https://psutil.readthedocs.io/)
- [Pydantic](https://docs.pydantic.dev/)
- [Python-dotenv](https://github.com/theskumar/python-dotenv)
- [FastAPI](https://fastapi.tiangolo.com/)
- [Uvicorn](https://www.uvicorn.org/)

## Troubleshooting
- Check service status: `sudo systemctl status pdfapp`
- View logs: `sudo journalctl -u pdfapp`
- Ensure all ports are correctly opened in AWS Security Group
- Verify environment variables are correctly set in the service file

