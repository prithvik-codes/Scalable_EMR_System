# db/models.py
from sqlalchemy import Column, Integer, String, DateTime, Float, Text, ForeignKey
from sqlalchemy.orm import relationship
import datetime
from .db import Base

class Patient(Base):
    __tablename__ = "patients"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    gender = Column(String(10))
    age = Column(Integer)
    contact = Column(String(50))
    address = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    vitals = relationship("Vitals", back_populates="patient", cascade="all, delete-orphan")
    records = relationship("MedicalRecord", back_populates="patient", cascade="all, delete-orphan")

class Vitals(Base):
    __tablename__ = "vitals"
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    heart_rate = Column(Integer)
    systolic = Column(Integer)
    diastolic = Column(Integer)
    temperature = Column(Float)
    oxygen = Column(Float)
    recorded_at = Column(DateTime, default=datetime.datetime.utcnow)

    patient = relationship("Patient", back_populates="vitals")

class MedicalRecord(Base):
    __tablename__ = "medical_records"
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    diagnosis = Column(Text)
    prescription = Column(Text)
    doctor = Column(String(100))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    patient = relationship("Patient", back_populates="records")

class Doctor(Base):
    __tablename__ = "doctors"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    specialization = Column(String)
    username = Column(String, unique=True)
    password = Column(String)
