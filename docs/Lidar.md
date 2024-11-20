Les Lidar utiliser par INTech sont des [UST-10LX](https://www.hokuyo-aut.jp/search/single.php?serial=167) concu et vendu par Hokuyo.<!-- Ce sont des lidar haut performance. --> Une documentation non officel (mais plutot complete existe [ici](https://sourceforge.net/p/urgnetwork/wiki/Home/)). ![an image showing a UST-10lx with an orange top. We can read Hokuyo Smart Urg underneath](img/UST-10lx.jpg "A UST-10lx Lidar")

<img src="/img/UST-10lx" alt="drawing" width="200"/>

Il communique par Ethernet en utilisant le protocole [Secure Communications Interoperability Protocol (SCIP)](https://en.wikipedia.org/wiki/Secure_Communications_Interoperability_Protocol). Ce protocol peut faire peur a premiere vue mais nous n'utilison que les commande decrit [ici](https://sourceforge.net/p/urgnetwork/wiki/scip_en/). Pour communiquer par ethernet, les lidar possede une adresse IP: 

```
192.168.0.10:10940/24
```

Il faut donc choisir une adresse ip dans le bon sous-resaux. Nous avons arbitrairement choisi:

```
192.168.0.11
```
