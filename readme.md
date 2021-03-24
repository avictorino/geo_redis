<h2>Resumo:</h2>
<p>Reescrever funcionalidade para calcular distancia entre lat/long utilizando REDIS (geospatial indexing) para milhões de registros.</p>

<h3>Problema:</h3> 
<p>
O problema original que me foi enviado pelo meu cliente é sobre o exesso de memória gasto em uma determinada aplicação para
calcular a distancia entre pontos ( latitudo / longitude ). No momento, a aplicação legada, 
incialmente mal dimensionada no momento do desenvolvimento, trazia uma quantidade de dados significativa para a memória 
para criar a estrutura de dados compatível com a funcionalidade.
</p>
<p>
No momento que eu iniciei a minha analise ao problema estava sendo carregado 
em memória algo em torno de >5mi < 10mi de registros em memória. 
</p>
<p>
Esse dados vinham de uma base analítica redshift, e claro, com milhões de linhas no baco de dados que 
por sua vez recebia uma importação do RDS(XXG) MySql de produção com +-40gb através de uma task do airflow.
</p>

<h3>Solução emergencial:</h3>
<p>
A minha primeira abordagem foi fazer uma query geospacial diretamente no redshift para reduzir 
a quantidade de dados em memória e restringindo somente pelas distâncias mais próximas, 
assim deixando o banco de dados fazer o trabalho pesado. Dessa forma o sistema volta a ao ar no mesmo dia.
</p>
<p>
Como o acesso era +-5 queries por segundo, era melhor ter esse fluxo no banco de dados 
por algumas semanas até que a solução definitiva implementada/implantada. 
Claro que a prioridade aumentou assim que descobri que outras três aplicações faziam a mesma carga para memória
exigindo cada vez mais recursos do datacenter.
</p>

'''sql
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
'''

###Solução definitiva
Foi criado alguns microserviços para dividir a carga e a responsabilidade da funcionalidade. 
A versão que temos a seguir é somente uma variação simplificada da solução original, que por sua vez utiliza uma base muito menor. 
load_data.py - Serviço que irá popular um banco de dados com registros fictícios incluindo geolocalizações.
worker.py - Rotina Celery que mantém os dados do redis atualizados com delay de 5 minutos
web.py interface http para receber requests para ambas as abordagens ( redis / postgis )
