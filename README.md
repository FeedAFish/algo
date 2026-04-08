<h1>Project</h1>
<h2>School project to emulate Airbnb</h2>

<p>To emulate Airbnb as closely as possible, we need to collect tourism-related data. We must use open datas from https://www.data.gouv.fr/
<br>
To meet this requirement, we are using DATAtourisme, an API that aggregates tourims-related data.
<br>
Here are the API documentation links:
<br>
https://api.datatourisme.fr/v1/docs
<br>
https://api.datatourisme.fr/v1/swagger/</p>

<h2>How to get an API's KEY</h2>
<h3>Authentication Key Acquisition :</h3>

<p>Get your key at https://info.datatourisme.fr/utiliser-les-donnees
<br>
The API uses a unique authentication key to secure requests. You can provide this key in two ways.
<br>
<br>
<em>Method 1: HTTP Header (Recommended)</em>
<br>
Include the key in the X-API-Key header of your request.
<br>
<code>X-API-Key: your_unique_api_key</code>
<br>
<br>
<em>Method 2: Query Parameter</em>
<br>
Add the key as the api_key parameter in the URL of your request.
<br>
<code>GET /v1/catalog?api_key=your_unique_api_key</code></p>


<h2>How to use the API's KEY</h2>
<p>Create a .env file in the root of your project and add it your key :
  <br>
  <br>
  <strong>Linux</strong>
    <br>
    <code>echo "export API_KEY=your_unique_api_key" > .env</code>
    <br>
    <br>
  <strong>Windows</strong>
  <br>
  <code>echo export API_KEY=your_api_key > .env</code>
  <br>
  <br>
  <strong>Make sure .env is added to your .gitignore</strong></p>

<h2>Installation</h2>
<h3>Clone the repository :</h3>
<code>git clone https://github.com/Algo-dev-ynov/Project.git
<br>
cd Project</code>

<h3>Create and activate a virtual environment :</h3>

<code>python -m venv venv</code>

<strong>Linux</strong>
<br>
<code>source venv/bin/activate</code>

<strong>Windows</strong>
<br>
<code>venv\Scripts\activate</code>
<br>

<h3>Install dependencies :</h3>
<strong>Linux</strong>
<br>
<code>pip3 install -r requirement.txt</code>
<br>
<br>
<strong>Windows</strong>
<br>
<code>pip install -r requirement.txt</code>
<br>
<br>

<h2>Creating a reproducible setup with Docker</h2>
<h3>How to give the API's key to the env :</h3>
<p>
  <strong>Linux</strong>
  <br>
  <code>export API_KEY=your_unique_api_key</code>
  <br>
  <br>
  <strong>Windows</strong>
  <br>
  <code>set API_KEY=your_unique_api_key</code>
</p>
<h3>How to start the docker :</h3>
<p>This command create an env
<br>
<code>docker compose -f docker-compose_downloader.yml up -d</code>
<br>
<br>
You must run the next command to start the download that will create the data lake :<br>
<code>docker compose -f docker-compose_downloader.yml exec -it airbnb python3 -m data_download</code></p>

<h3>Unitest and deploiyment test :</h3>
<p>This command runs unitest and deployment test
<br>
<code>docker compose -f docker-compose_downloader.yml exec -it airbnb pytest</code></p>
<br>
<br>
<br>


<h2>MongoDB Setup and Data Loading</h2>

<h3>1. Start MongoDB Service</h3>
<p>Run MongoDB using Docker Compose:
<br>
<code>docker-compose up mongodb</code>
<br>
This starts MongoDB locally on <code>localhost:27017</code></p>

<h3>2. Download Raw Data</h3>
<p>If you don't want to re-run the scraping from the API, download the pre-scraped data:
<br>
<strong>Download Link:</strong> <a href="https://drive.google.com/file/d/1rsxMfRzyVyzccLkRFxgwpKknGCqvcR1a/view?usp=sharing">DATAtourisme Data (Google Drive)</a>
<br>


<h3>3. Load Data into MongoDB</h3>
<p>Run the data loader to process and insert data into MongoDB:
<br>
<code>python data_loader</code>
<br>
<br>
This will:
<br>
- Step 1: Read raw data from <code>./API/data_raw_ndjson/</code> and insert into <code>place_raw</code>
<br>
- Step 2: Transform and clean data, insert into <code>place_clean</code>
<br>
- Step 3: Generate ratings (11 loops with varying coverage)
<br>
<br>
You can skip to a specific step using:
<br>
<code>python -m data_loader 2</code> (skip step 1, start from step 2)
<br>
<code>python -m data_loader 3</code> (skip steps 1-2, only generate ratings)</p>

<h3>4. View Data</h3>
<p>Connect to MongoDB at <code>mongodb://root:root@localhost:27017/</code> using MongoDB Compass to view data in the <code>tourisme_data</code> database with collections:
<br>
- <code>place_raw</code>: Original raw data from the API
<br>
- <code>place_clean</code>: Cleaned, structured data with fields: _id, label, type, geo, address, description, contact, price, uuid, uri
<br>
- <code>place_ratings</code>: Ratings data with fields: uuid, rating (1-5), comment</p>
