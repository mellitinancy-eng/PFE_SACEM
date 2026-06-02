@echo off
set PGPASSWORD=azerty

"C:\Program Files\PostgreSQL\17\bin\pg_dump.exe" -U postgres -h localhost -p 5434 sacem_db > backup_sacem.sql

echo Backup termine !
pause