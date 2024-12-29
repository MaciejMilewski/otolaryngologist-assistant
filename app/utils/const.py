typ_badan = [
    {'id': '1', 'name': 'Badanie profilaktyczne nauczycieli'},
    {'id': '2', 'name': 'Badanie profilaktyczne na wysokość'},
    {'id': '3', 'name': 'Badanie przed operacją tarczycy'},
    {'id': '4', 'name': 'Badanie przed operacją kolana'},
    {'id': '5', 'name': 'Badanie przed operacją stawu biodrowego'},
    {'id': '6', 'name': 'Badanie przed operacją przeszczepu'},
    {'id': '7', 'name': 'Badanie przed leczeniem biologicznym'},
    {'id': '8', 'name': 'Badanie przed operacją zaćmy'},
    {'id': '9', 'name': 'Badanie profilaktyczne kierowców kategorii B'},
    {'id': '10', 'name': 'Badanie profilaktyczne kierowców kategorii C+E'},
    {'id': '11', 'name': 'Zaświadczenie o stanie zdrowia'}
]
place = [
    {'id': '1', 'name': 'Pruszcz Gdański'},
    {'id': '2', 'name': 'Starogard Gdański'},
    {'id': '3', 'name': 'Gdańsk'},
    {'id': '4', 'name': 'Sopot'},
    {'id': '5', 'name': 'Tczew'},
]
typ_messages = {
                    '1': "W badaniu laryngologicznym wykonanym w dniu dzisiejszym nie stwierdzono istotnych przeciwwskazań do dalszej pracy w charakterze nauczyciela.",
                    '2': "W badaniu laryngologicznym wykonanym w dniu dzisiejszym nie stwierdzono przeciwwskazań do pracy na wysokości powyżej trzech metrów.",
                    '3': "W badaniu laryngologicznym w dniu dzisiejszym nie stwierdzono przeciwwskazań laryngologicznych do operacji tarczycy. Ruchomość fałdów głosowych prawidłowa.",
                    '4': "W badaniu laryngologicznym w dniu dzisiejszym nie stwierdzono przeciwwskazań laryngologicznych do operacji kolana.",
                    '5': "W badaniu laryngologicznym w dniu dzisiejszym nie stwierdzono przeciwwskazań laryngologicznych do operacji stawu biodrowego.",
                    '6': "W badaniu laryngologicznym w dniu dzisiejszym nie stwierdzono przeciwwskazań laryngologicznych do operacji przeszczepu.",
                    '7': "W badaniu laryngologicznym w dniu dzisiejszym nie stwierdzono przeciwwskazań laryngologicznych do leczenia biologicznego.",
                    '8': "W badaniu laryngologicznym w dniu dzisiejszym nie stwierdzono przeciwwskazań laryngologicznych do operacji zaćmy.",
                    '9': "W badaniu laryngologicznym w dniu dzisiejszym nie stwierdzono przeciwwskazań laryngologicznych do pracy jako kierowca kategorii B. ",
                    '10': "W badaniu laryngologicznym w dniu dzisiejszym nie stwierdzono przeciwwskazań laryngologicznych do pracy jako kierowca kategorii C+E.",
 }
typ_messages_no = {
                    '1': "W badaniu laryngologicznym wykonanym w dniu dzisiejszym stwierdzono istotne przeciwwskazania do pracy w charakterze nauczyciela.",
                    '2': "W badaniu laryngologicznym wykonanym w dniu dzisiejszym stwierdzono przeciwwskazania do pracy na wysokości powyżej trzech metrów.",
                    '3': "W badaniu laryngologicznym stwierdzono w dniu dzisiejszym przeciwwskazania do planowej operacji tarczycy.",
                    '4': "W badaniu laryngologicznym w dniu dzisiejszym stwierdzono przeciwwskazania do planowej operacji kolana.",
                    '5': "W badaniu laryngologicznym w dniu dzisiejszym stwierdzono przeciwwskazania do planowej operacji stawu biodrowego.",
                    '6': "W badaniu laryngologicznym w dniu dzisiejszym stwierdzono przeciwwskazania do planowej operacji przeszczepu.",
                    '7': "W badaniu laryngologicznym w dniu dzisiejszym stwierdzono przeciwwskazania do planowego leczenia biologicznego.",
                    '8': "W badaniu laryngologicznym w dniu dzisiejszym stwierdzono przeciwwskazania do planowej operacji zaćmy.",
                    '9': "W badaniu laryngologicznym w dniu dzisiejszym stwierdzono przeciwwskazania laryngologiczne do pracy jako kierowca kategorii B.",
                    '10': "W badaniu laryngologicznym w dniu dzisiejszym stwierdzono przeciwwskazania laryngologiczne do pracy jako kierowca kategorii C+E.",
}

place = [
    {'id': '1', 'name': 'Pruszcz Gdański'},
    {'id': '2', 'name': 'Starogard Gdański'},
    {'id': '3', 'name': 'Gdańsk'},
    {'id': '4', 'name': 'Sopot'},
    {'id': '5', 'name': 'Tczew'},
    {'id': '6', 'name': 'Gdynia'}
]


W0 = {
      'W01 -  48 pkt': 'Porada pohospitalizacyjna - do 30 dni od wypisu',
      'W02 -  11 pkt': 'Porada receptowa',
      'W11 -  44 pkt': 'Porada I typu: W1 / 2xW1',
      'W12 -  75 pkt': 'Porada II typu: 3xW1 / W2',
      'W13 - 133 pkt': 'Porada III typu: 3xW1 + W2 / W2 + W16 / 2xW2 / W3',
      'W14 - 172 pkt': 'Porada IV typu: 3xW1 + W3 / 2xW3 / 2xW10',
      'W15 -  56 pkt': 'Porada V typu: W16 (Histopatologia)',
      'W17 - 104 pkt': 'Porada VII typu: W9 / W10 (USG Doppler)',
      'W31 -  82 pkt': 'Porada udzielana w miejscu pobytu świadczeniobiorcy'
}

W1 = {
      '20.391': 'Posturografia',
      '21.293': 'Rinoskopia tylna',
      '31.42': 'Laryngoskopia i inne wziernikowanie tchawicy',
      '87.164': 'Rtg zatok nosa',
      '87.165': 'Rtg nosa',
      '95.413': 'Badanie odruchu strzemiączkowego',
      '95.415': 'Tympanometria',
      '95.45': 'Test obrotowy',
      '95.48': 'Dopasowanie aparatu słuchowego',
      '99.9960': 'Próby kaloryczne',
      '99.9970': 'Gustometria swoista',
      '99.9971': 'Elektrogustometria',
      '99.9975': 'Olfaktometria podmuchowa',
      '99.9976': 'Psychofizyczny test identyfikacji zapachów',
      '99.9977': 'Badanie węchu zestawem markerów'
}

W2 = {
      '87.092': 'Rtg krtani bez kontrastu – zdjęcia warstwowe',
      '87.093': 'Rtg przewodu nosowo – łzowego z kontrastem',
      '87.094': 'Rtg nosogardzieli bez kontrastu',
      '87.095': 'Rtg gruczołów ślinowych bez kontrastu',
      '87.098': 'Rtg gruczołów ślinowych z kontrastem',
      '87.11': 'Rtg panoramiczne zębów',
      '87.174': 'Rtg twarzoczaszki – przeglądowe',
      '87.175': 'Rtg twarzoczaszki – celowane lub czynnościowe',
      '87.176': 'Rtg czaszki – przeglądowe',
      '87.177': 'Rtg czaszki – celowane lub czynnościowe',
      '87.221': 'Rtg kręgosłupa odcinka szyjnego – przeglądowe',
      '87.222': 'Rtg kręgosłupa odcinka szyjnego – celowane lub czynnościowe',
      '87.440': 'Rtg klatki piersiowej',
      '87.495': 'Rtg śródpiersia',
      '87.496': 'Rtg tchawicy',
      '87.691': 'Rtg przełyku z kontrastem',
      '88.717': 'USG ślinianek',
      '88.719': 'USG krtani',
      '88.790': 'USG węzłów chłonnych',
      '89.121': 'Rhinomanometria',
      '91.821': 'Badanie materiału biologicznego – posiew jakościowy i ilościowy',
      '91.831': 'Badanie materiału biologicznego – posiew jakościowy wraz z identyfikacją drobnoustroju',
      '91.841': 'Badanie mikroskopowe materiału biologicznego – parazytologia',
      '95.241': 'Elektronystagmogram (ENG)',
      '95.242': 'Video ENG',
      '95.412': 'Audiometria impedancyjna',
      '95.414': 'Subiektywna audiometria',
      '95.436': 'Otoemisja akustyczna',
      '99.9955': 'Próby nadprogowe'
}

W3 = {
      '29.1901': 'Stroboskopia',
      '29.1902': 'Videostroboskopia',
      '89.152': 'Somatosensoryczne potencjały wywołane (SEP)',
      '89.153': 'Słuchowe potencjały wywołane z pnia mózgu (BAEP)',
}

W9 = {
      '88.716': 'Badanie USG przezczaszkowe - Doppler'
}

W10 = {
      '88.714': 'Badanie USG głównych naczyń szyi - Doppler'
}

W16 = {
      '91.447': 'Badanie mikroskopowe materiału biologicznego – badanie cytologiczne',
      '91.891': 'Badanie mikroskopowe materiału biologicznego – preparat bezpośredni'
}
