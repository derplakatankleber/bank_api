"""Banking specific data models."""

from __future__ import annotations

from typing import List, Optional

from dataclasses import dataclass, field

from .common import (
    AccountInformation,
    AggregatedInfo,
    AmountValue,
    CurrencyString,
    DateString,
    EnumText,
    ModelDumpMixin,
    PagingInfo,
    _coerce_optional_str,
)


@dataclass
class Account(ModelDumpMixin):
    """Master data of an account."""

    accountId: Optional[str] = None
    accountDisplayId: Optional[str] = None
    currency: Optional[CurrencyString] = None
    clientId: Optional[str] = None
    accountType: Optional[EnumText] = None
    iban: Optional[str] = None
    creditLimit: Optional[AmountValue] = None

    @classmethod
    def model_validate(cls, value: object) -> Optional["Account"]:
        if value is None or isinstance(value, cls):
            return value
        if isinstance(value, dict):
            return cls(
                accountId=_coerce_optional_str(value.get("accountId")),
                accountDisplayId=_coerce_optional_str(value.get("accountDisplayId")),
                currency=CurrencyString.model_validate(value.get("currency")),
                clientId=_coerce_optional_str(value.get("clientId")),
                accountType=EnumText.model_validate(value.get("accountType")),
                iban=_coerce_optional_str(value.get("iban")),
                creditLimit=AmountValue.model_validate(value.get("creditLimit")),
            )
        raise TypeError(f"Cannot convert {value!r} to Account")


@dataclass
class AccountBalance(ModelDumpMixin):
    """Account information, including cash balance and buying power."""

    account: Optional[Account] = None
    accountId: Optional[str] = None
    balance: Optional[AmountValue] = None
    balanceEUR: Optional[AmountValue] = None
    availableCashAmount: Optional[AmountValue] = None
    availableCashAmountEUR: Optional[AmountValue] = None

    @classmethod
    def model_validate(cls, value: object) -> "AccountBalance":
        if isinstance(value, cls):
            return value
        if isinstance(value, dict):
            return cls(
                account=Account.model_validate(value.get("account")),
                accountId=_coerce_optional_str(value.get("accountId")),
                balance=AmountValue.model_validate(value.get("balance")),
                balanceEUR=AmountValue.model_validate(value.get("balanceEUR")),
                availableCashAmount=AmountValue.model_validate(
                    value.get("availableCashAmount")
                ),
                availableCashAmountEUR=AmountValue.model_validate(
                    value.get("availableCashAmountEUR")
                ),
            )
        raise TypeError(f"Cannot convert {value!r} to AccountBalance")


@dataclass
class ListResourceAccountBalance(ModelDumpMixin):
    """List wrapper for account balances."""

    paging: Optional[PagingInfo] = None
    aggregated: Optional[AggregatedInfo] = None
    values: List[AccountBalance] = field(default_factory=list)

    @classmethod
    def model_validate(cls, value: object) -> "ListResourceAccountBalance":
        if isinstance(value, cls):
            return value
        if isinstance(value, dict):
            return cls(
                paging=PagingInfo.model_validate(value.get("paging")),
                aggregated=AggregatedInfo.model_validate(value.get("aggregated")),
                values=[
                    AccountBalance.model_validate(item)
                    for item in value.get("values", [])
                    if item is not None
                ],
            )
        raise TypeError(
            f"Cannot convert {value!r} to ListResourceAccountBalance"
        )


@dataclass
class AccountTransaction(ModelDumpMixin):
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

    @classmethod
    def model_validate(cls, value: object) -> "AccountTransaction":
        if isinstance(value, cls):
            return value
        if isinstance(value, dict):
            return cls(
                reference=_coerce_optional_str(value.get("reference")),
                bookingStatus=_coerce_optional_str(value.get("bookingStatus")),
                bookingDate=DateString.model_validate(value.get("bookingDate")),
                amount=AmountValue.model_validate(value.get("amount")),
                remitter=AccountInformation.model_validate(value.get("remitter")),
                deptor=AccountInformation.model_validate(value.get("deptor")),
                creditor=AccountInformation.model_validate(value.get("creditor")),
                valutaDate=_coerce_optional_str(value.get("valutaDate")),
                directDebitCreditorId=_coerce_optional_str(
                    value.get("directDebitCreditorId")
                ),
                directDebitMandateId=_coerce_optional_str(
                    value.get("directDebitMandateId")
                ),
                endToEndReference=_coerce_optional_str(value.get("endToEndReference")),
                newTransaction=value.get("newTransaction"),
                remittanceInfo=_coerce_optional_str(value.get("remittanceInfo")),
                transactionType=EnumText.model_validate(value.get("transactionType")),
            )
        raise TypeError(f"Cannot convert {value!r} to AccountTransaction")


@dataclass
class ListResourceAccountTransaction(ModelDumpMixin):
    """List wrapper for account transactions."""

    paging: Optional[PagingInfo] = None
    aggregated: Optional[AggregatedInfo] = None
    values: List[AccountTransaction] = field(default_factory=list)

    @classmethod
    def model_validate(cls, value: object) -> "ListResourceAccountTransaction":
        if isinstance(value, cls):
            return value
        if isinstance(value, dict):
            return cls(
                paging=PagingInfo.model_validate(value.get("paging")),
                aggregated=AggregatedInfo.model_validate(value.get("aggregated")),
                values=[
                    AccountTransaction.model_validate(item)
                    for item in value.get("values", [])
                    if item is not None
                ],
            )
        raise TypeError(
            f"Cannot convert {value!r} to ListResourceAccountTransaction"
        )
