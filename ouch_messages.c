#ifndef OUCH_MESSAGES_H
#define OUCH_MESSAGES_H

#include <string.h>
#include <iostream>
#include <fstream>


enum class buy_sell_indicator {BUY = 'B', SELL = 'S'};


typedef struct enter_order_message{
    buy_sell_indicator indicator;
    
    //Stock symbol
    char stock[8];

    //Total number of shares
    int shares;

    //6 whole number digits followed by 4 decimal digits
    int price;
} enter_order_message;












#endif // OUCH_MESSAGES_H