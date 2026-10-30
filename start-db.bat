@echo off
title Local Postgres Server
echo Starting Local PostgreSQL Server...
"D:\loan-default-predictor\Postgresql\pgsql\bin\postgres.exe" -D "D:\loan-default-predictor\loan-risk\predictor\Postgresql\pgsql\data"
pause
