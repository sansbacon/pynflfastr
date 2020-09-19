# Contests Documentation

The contests resource is at https://www.draftkings.com/lobby/getcontests?sport=NFL

The text of the page is JSON, is a dict when parsed into python data structure

## Top-Level Keys

* Contests
* DepositTransaction
* DirectChallengeModal
* DraftGroups
* GameSets
* GameTypes
* IsVip
* MarketingOffers
* PrizeRedemptionModel
* PrizeRedemptionPop
* SelectedSport
* SelectedSportId
* ShowAds
* ShowRafLink
* SportMenuItems
* UseJSWebLobbyModals
* UseRaptorHeadToHead
* UserGeoLocation

### Contests (list)

This is a long list (7060 last time I checked)

```javascript
{
    "a": 5,
    "attr": {
        "IsGuaranteed": "true",
        "IsStarred": "true",
        "IsTournamentOfChamp": "true",
        "LobbyClass": "icon-millionaire"
    },
    "crownAmount": 2750,
    "cs": 1,
    "cso": 0,
    "dg": 37493,
    "dgpo": 23945979.8,
    "ec": 0,
    "fpp": 5,
    "freeWithCrowns": true,
    "fwt": true,
    "gameType": "Classic",
    "id": 89073497,
    "ir": 1,
    "isBonusFinalized": false,
    "isOwner": false,
    "isSnakeDraft": false,
    "m": 1195005,
    "mec": 150,
    "n": "NFL $5M Fantasy Football Millionaire [$1M to 1st]",
    "nt": 744327,
    "pd": {
        "Cash": "5000000",
        "Ticket": "1 Ticket"
    },
    "po": 5025000.0,
    "pt": 1,
    "rl": false,
    "rlc": 0,
    "rll": 99999,
    "s": 1,
    "sa": true,
    "sd": "/Date(1600016400000)/",
    "sdstring": "Sun 1:00PM",
    "so": -99999999,
    "ssd": null,
    "startTimeType": 0,
    "tix": false,
    "tmpl": 364053,
    "uc": 0,
    "ulc": 3
}
```

* Relevant keys
  - dg (int): this is draftgroup_id, here 37493
    If you loop through the relevant draftgroups, can get all the relevant contests
    In: set([item['dg'] for item in data['Contests'] if item['gameType'] == 'Classic'])          
    Out: {37493, 38119, 38121, 38122, 38123, 38124}
    https://www.draftkings.com/lobby#/NFL/37493/All --> Main Slate
    https://www.draftkings.com/lobby#/NFL/38121/All --> Early Only
    
  - id (int): contest_id, here 89073497
  - m (int): the contest size, here 1195005 (Milly Maker is large)
  - n (str): the contest name, here NFL $5M Fantasy Football Millionaire
  - p (int): the prize pool, here 5025000.0 (~ $5 Million)
  - sd (str): string in the format /Date(epoch GMT in milliseconds)/
      datetime.datetime.fromtimestamp(1600016400000/1000) 
      datetime.datetime(2020, 9, 13, 12, 0)
  - sdstring (str): start time, here Sun 1:00PM. Can use to split slates.
  - gameType (str):
    - In-Game Showdown (H2)
    - Classic
    - KFC Sunday Night Series
    - Showdown Captain Mode
    - Madden Showdown Captain Mode
    - Tiers
    - Madden Classic
  - isSnakeDraft (bool): can filter bestball drafts

* Contest Name & Game Set

Contest name has the Game Set in it, except for main slate
  - Early Only
  - Sun-Mon
  - 2H xxx (these are second-half showdowns)
  - Afternoon Only
  - TEAM vs TEAM (these are showdowns)
  - Afternoon Turbo
  - Primetime
  - Madden Stream TEAM vs TEAM
  - Madden Stream
  - Thu-Mon
