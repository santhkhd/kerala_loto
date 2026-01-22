@echo off
cd /d "c:\Users\santh\Downloads\keralaloto\backup\kerala_loto-main"
echo Starting Update: %date% %time% >> local_run.log
python updateloto.py >> local_run.log 2>&1
python generate_manifest.py >> local_run.log 2>&1
python generate_history.py >> local_run.log 2>&1
python generate_pdf_links.py >> local_run.log 2>&1
python blogger_publish.py >> local_run.log 2>&1
git add .
git commit -m "Auto Update Local"
git push origin main
echo Done.
