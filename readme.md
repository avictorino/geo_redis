### Summary:
Rewriting functionality to calculate lat / long distance, these coordinates were in an analytical database with 5mi records and it would not be prudent to let external requests execute this query.

#### Problem:
The problem reported was the excess use of memory used in a given application to calculate the distance between geographical points. At the moment, the legacy application loads a significant amount of data to memory and later perform a find operation on the structure through a GIS library.
  
When I started to analyze the problem, it was being loaded into memory using somewhere around> 5mi & <10mi of records in memory, due to the rapid growth of the company in the last few months.
  
#### Emergency solution:
My first approach was to do a geospatial query directly on the database and reduce the amount of data in memory, limiting it only by the closest distances, consequently letting the database deal with the heavy lifting. The system goes back to air on the same day.

    select 
        profile_id, 
        ST_MAKEPOINT({latitude}, {longitude}) as request_center, 
        CAST (
            ST_DISTANCESPHERE (
                request_center,
                ST_MAKEPOINT (p.latitude, p.longitude)
                ) AS INTEGER
            ) AS distance
        from profiles as p
        where distance <= '{radius_mts * 1000}'
    order by distance;
    ** simplified version for ilustrated propose
  
The actual query per second was +-5, it was better to have this flow in the database for a few weeks until the final solution was implemented/deployed.

Of course, the priority to move for a scalable solution increased as soon as I discovered that three other applications were doing the same load on memory, demanding more and more resources from the EC2s servers each one with 16GB.
    

### Definitive solution
Using REDIS with its geo index functionality, I stored all the coordinates already filtered by the main attribute, thus creating a structure in Redis with the following format:

    ##### / cpp-developers /
     - developer_id: 1234
     - developer_id: 4345
     - developer_id: 6544
     - developer_id: 98
    ##### / python-developer /
     - developer_id: 1234
     - developer_id: 4345
     - developer_id: 8975

  
Each geo_index categorized in Redis maintains includes +- 5000 records, allowing each geospatial query to be executed in 100 milliseconds, faster than 1-second spends by the database, and mutch large scalable solution.

  
#### Repository architecture:
I wrote some microservices to spread the responsibility for this functionality. The repository version is just a simplified variation of the original solution, which uses a much larger databasebase/complexity.
  
** load_data.py ** - Service that will populate a database with fictitious records with geolocations.
  
** worker.py ** - Celery routine that keeps the Redis data up to date with a 5-minute delay.
  
** web.py ** - http interface to receive requests for both approaches (redis / postgis)


#### RUN
    $docker-compose up

Will create a specific container for Redis and Postgis, then start to populate PostGIS and copy the Redis geoindex.

The web interface exposes two different endpoints, with the same result, just to compare both solutions:

##### POSTGIS Query
    http://127.0.0.1:5000/postgis_profiles/33.7207/-116.21677/100/km

##### GEO REDIS Query
    http://127.0.0.1:5000/georedis_profiles/33.7207/-116.21677/100/km

