git pull -q
python3 graph.py &> /dev/null
git commit -q -a -m "update returns"
git push -q
