"""Banking specific data models."""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field

from .common import (
    AccountInformation,
    AggregatedInfo,
    AmountValue,
    CurrencyString,
    DateString,
    EnumText,
    PagingInfo,
)


class Account(BaseModel):
    """Master data of an account."""

    accountId: Optional[str] = None
    accountDisplayId: Optional[str] = None
    currency: Optional[CurrencyString] = None
    clientId: Optional[str] = None
    accountType: Optional[EnumText] = None
    iban: Optional[str] = None
    creditLimit: Optional[AmountValue] = None


class AccountBalance(BaseModel):
    """Account information, including cash balance and buying power."""

    account: Optional[Account] = None
    accountId: Optional[str] = None
    balance: Optional[AmountValue] = None
    balanceEUR: Optional[AmountValue] = None
    availableCashAmount: Optional[AmountValue] = None
    availableCashAmountEUR: Optional[AmountValue] = None


class ListResourceAccountBalance(BaseModel):
    """List wrapper for account balances."""

    paging: Optional[PagingInfo] = None
    aggregated: Optional[AggregatedInfo] = None
    values: List[AccountBalance] = Field(default_factory=list)


class AccountTransaction(BaseModel):
    """Model for an account transaction."""

    reference: Optional[str] = None
    bookingStatus: Optional[str] = None
    bookingDate: Optional[DateString] = None
    amount: Optional[AmountValue] = None
    remitter: Optional[AccountInformation] = None
    deptor: Optional[AccountInformation] = None
    creditor: Optional[AccountInformation] = None
    valutaDate: Optional[str] = None
    directDebitCreditorId: Optional[str] = None
    directDebitMandateId: Optional[str] = None
    endToEndReference: Optional[str] = None
    newTransaction: Optional[bool] = None
    remittanceInfo: Optional[str] = None
    transactionType: Optional[EnumText] = None


class ListResourceAccountTransaction(BaseModel):
    """List wrapper for account transactions."""

    paging: Optional[PagingInfo] = None
    aggregated: Optional[AggregatedInfo] = None
    values: List[AccountTransaction] = Field(default_factory=list)
