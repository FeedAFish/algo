<h1> How this section works ?</h1>

<h2>Script</h2>

<p>First of all, you have to be at the root of the project otherwise it won't work. You have to install all the dependencies first with this line :<br>
<code>pip install -r requirements.txt</code>
<br><br></p>

<p>After the download completed, you have to run the script with this line :
<br>
<br>
<strong>Linux</strong>
<br>
<code>python3 -m data_download</code>
<br>
<br>
<strong>Windows</strong>
<br>
<code>python -m data_download</code>
</p>
<br>

<h2>Tree</h2>

<p>
<code>.
  ├── __main__.py # Entry point of the application
  ├── README.md
  └── script # Folder containing all Python scripts
      ├── datatourisme_download.py # Download raw data from the DATAtourisme API
      ├── __init__.py
      └── picture.py # Download images from raw data</code>
</p>

