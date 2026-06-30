export const TYPE_REASONS = {
  FULL_NAME: 'A full name can directly identify a specific person.',
  FIRST_NAME: 'A first name, combined with other details, can identify someone.',
  LAST_NAME: 'A last name narrows identification, especially with context.',
  EMAIL: 'An email address is a unique identifier that directly maps to one person.',
  PHONE: 'A phone number is a direct personal identifier tied to an individual.',
  ADDRESS: 'A physical address reveals where someone lives or works.',
  STREET: 'A street name is part of a physical address that locates someone.',
  CITY: 'A city name, combined with other details, helps locate someone.',
  STATE: 'A state or region, combined with other details, narrows location.',
  ZIP_CODE: 'A zip or postal code narrows someone to a small geographic area.',
  SSN: 'A Social Security Number is a uniquely assigned government identifier.',
  DATE_OF_BIRTH: 'A date of birth is a key identifier used in identity verification.',
  MEDICAL_RECORD_NUMBER: 'A medical record number links to private health data.',
  DIAGNOSIS: 'A medical diagnosis is protected health information under HIPAA.',
  MEDICATION: 'Medication details reveal private health conditions.',
  INSURANCE_ID: 'An insurance ID links to personal health and financial records.',
  ACCOUNT_NUMBER: 'A bank account number gives direct access to financial identity.',
  ROUTING_NUMBER: 'A routing number, paired with account data, identifies a bank relationship.',
  CREDIT_CARD_NUMBER: 'A credit card number is a financial identifier that must be protected.',
  URL: 'A URL can contain personal identifiers like usernames or profile links.',
  IP_ADDRESS: 'An IP address can be used to trace online activity to a location.',
  USERNAME: 'A username can be linked across platforms to identify a person.',
  PASSWORD: 'A password is a private credential that must never be exposed.',
  ORGANIZATION_NAME: 'An organization name, in context, can narrow who someone is.',
  NPI: 'A National Provider Identifier uniquely identifies a healthcare provider.',
  BUILDING_NUMBER: 'A building number is part of a precise physical address.',
  COUNTRY: 'A country name, combined with other details, helps locate someone.',
  FINANCIAL_ID: 'A financial identifier links to specific accounts or registrations.',
  DATE: 'A date, in context with other details, can help identify someone.',
  DOMAIN: 'A domain name can be linked to a specific organization or individual.',
};

export const CATEGORY_NAMES = {
  FIRST_NAME: 'Names',
  LAST_NAME: 'Names',
  FULL_NAME: 'Names',
  EMAIL: 'Email Addresses',
  PHONE: 'Phone Numbers',
  ADDRESS: 'Addresses',
  STREET: 'Addresses',
  CITY: 'Addresses',
  STATE: 'Addresses',
  ZIP_CODE: 'Addresses',
  COUNTRY: 'Addresses',
  BUILDING_NUMBER: 'Addresses',
  SSN: 'Social Security Numbers',
  DATE_OF_BIRTH: 'Dates of Birth',
  MEDICAL_RECORD_NUMBER: 'Medical Record Numbers',
  DIAGNOSIS: 'Medical Diagnoses',
  MEDICATION: 'Medications',
  INSURANCE_ID: 'Insurance Information',
  ACCOUNT_NUMBER: 'Financial Account Numbers',
  ROUTING_NUMBER: 'Financial Routing Numbers',
  CREDIT_CARD_NUMBER: 'Credit Card Numbers',
  URL: 'Web URLs',
  IP_ADDRESS: 'IP Addresses',
  USERNAME: 'Usernames',
  PASSWORD: 'Passwords',
  ORGANIZATION_NAME: 'Organization Names',
  NPI: 'Provider IDs',
  FINANCIAL_ID: 'Financial IDs',
};

export const FINDING_EXPLANATIONS = {
  CLEAN: 'Clean means the verifier reviewed that part and did not see exposed personal information.',
  RISK: 'Risk means the text may still help identify someone when combined with other remaining details.',
  MISS: 'Miss means the verifier found personal information that should have been hidden but was left visible.',
};

export function humanizeEntityType(entityType) {
  return entityType
    .replace(/_/g, ' ')
    .toLowerCase()
    .replace(/\b\w/g, c => c.toUpperCase());
}

export function getReasonForType(entityType) {
  return TYPE_REASONS[entityType] || `This was identified as ${humanizeEntityType(entityType).toLowerCase()}, which could help identify someone.`;
}

export function getCategoryForType(entityType) {
  return CATEGORY_NAMES[entityType] || humanizeEntityType(entityType);
}

export function explainFindingType(type) {
  return FINDING_EXPLANATIONS[type] || 'Info means the system recorded an audit event for transparency.';
}
