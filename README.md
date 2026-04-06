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
<h3>Authentication Key Acquisition</h3>

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
    <code>echo "API_KEY=your_unique_api_key" > .env</code>
    <br>
    <br>
  <strong>Windows</strong>
  <br>
  <code>echo API_KEY=your_api_key > .env</code>
  <br>
  <br>
  <strong>Make sure .env is added to your .gitignore</strong></p>

<h2>Installation</h2>
<h3>Clone the repository:</h3>

<code>git clone https://github.com/Algo-dev-ynov/Project/
  cd https://github.com/Algo-dev-ynov/Project/</code>

<h3>Create and activate a virtual environment</h3>

<code>python -m venv venv</code>

<strong>Linux</strong>
<br>
<code>source venv/bin/activate</code>

<strong>Windows</strong>
<br>
<code>venv\Scripts\activate</code>

<h3>Install dependencies</h3>
<strong>Linux</strong>
<br>
<code>pip3 install -r requirement.txt</code>
<br>
<br>
<strong>Windows</strong>
<br>
<code>pip install -r requirement.txt</code>
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
<br>
Extract the downloaded file and place it in the project:
<br>
<code>./API/data_raw_ndjson/</code></p>

<h3>3. Load Data into MongoDB</h3>
<p>Run the data loader to insert data into MongoDB:
<br>
<code>python data_loader</code>
<br>
<br>
This will:
<br>
- Read raw data from <code>./API/data_raw_ndjson/</code> (Step 1)
<br>
- Transform and structure the data
<br>
- Insert into MongoDB <code>tourisme_data</code> database with two collections (Step 2):
<br>
&nbsp;&nbsp;&nbsp;&nbsp;- <code>place_raw</code>: Original raw data from the API
<br>
&nbsp;&nbsp;&nbsp;&nbsp;- <code>place_clean</code>: Cleaned and structured data</p>
- Add ratings randomized for demonstration. (Step 3)

**Note :** You can add a number after the command to skip directly to another step (ex. <code>python data_loader 3</code>)

<h3>4. View Data</h3>
<p>Connect to MongoDB at <code>mongodb://root:root@localhost:27017/</code> using any MongoDB client (e.g., MongoDB Compass) to view the data in the <code>tourisme_data</code> database.</p>