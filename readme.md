
### Resumo:
Reescrever funcionalidade para calcular distancia entre lat/long,   
essas coordenadas estavam em um banco de dados analítico com 5mi registros   
e não seria prudente deixar requests externos executar essa query  
#### Problema:   
O problema reportado pelo meu cliente é sobre o excesso de memória utilizado em uma determinada aplicação para calcular a distancia entre pontos ( latitude / longitude ). No momento, a aplicação legada, trazia uma quantidade de dados significativa para a memória e assim era inicializado a estrutura de dados compatível com a funcionalidade. 
No momento que eu iniciei a minha analise ao problema estava sendo carregado em memória algo em torno de >5mi && <10mi de registros em memória. 
Esse dados vinham de uma base analítica redshift, e claro, com milhões de linhas no baco de dados que   
por sua vez recebia uma importação do RDS(XXG) MySql de produção com +-40gb através de uma task do airflow. 
#### Solução emergencial:
A minha primeira abordagem foi fazer uma query geospacial diretamente no redshift para reduzir   
a quantidade de dados em memória e restringindo somente pelas distâncias mais próximas,   
assim deixando o banco de dados fazer o trabalho pesado. Dessa forma o sistema volta a ao ar no mesmo dia.  

Como o acesso era +-5 queries por segundo, era melhor ter esse fluxo no banco de dados   
por algumas semanas até que a solução definitiva implementada/implantada.   
Claro que a prioridade aumentou assim que descobri que outras três aplicações faziam a mesma carga para memória  
exigindo cada vez mais recursos do datacenter.
   
    select profile_id, ST_MAKEPOINT({latitude}, {longitude}) as request_center,  
        CAST(  
            ST_DISTANCESPHERE(  
                request_center,   
                ST_MAKEPOINT(p.latitude , p.longitude)  
                ) AS INTEGER  
            ) AS distance  
        from profiles as p  
        where distance <= '{radius_mts * 1000}'  
        order by distance;  

### Solução definitiva
Foi criado alguns microserviços para dividir a carga e a responsabilidade da funcionalidade.   
A versão que temos a seguir é somente uma variação simplificada da solução original, que por sua vez utiliza uma base muito menor.   

load_data.py - Serviço que irá popular um banco de dados com registros fictícios incluindo geolocalizações.  
worker.py - Rotina Celery que mantém os dados do redis atualizados com delay de 5 minutos  
web.py interface http para receber requests para ambas as abordagens ( redis / postgis )