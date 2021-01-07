git pull -q
python3 stats.py
git commit -q -a -m "update returns" &> /dev/null
git push -q
