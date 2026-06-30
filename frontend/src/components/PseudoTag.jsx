import { useState, useRef, useEffect } from 'react';

// Why each entity type gets flagged - plain language reasons for Marcus
const TYPE_REASONS = {
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

function getReasonForType(entityType) {
  return TYPE_REASONS[entityType] || `This was identified as ${entityType.replace(/_/g, ' ').toLowerCase()}, which is personally identifiable information that could help identify someone.`;
}

export default function PseudoTag({ entity }) {
  const [expanded, setExpanded] = useState(false);
  const tagRef = useRef(null);

  // Close on outside click
  useEffect(() => {
    if (!expanded) return;
    const handleClick = (e) => {
      if (tagRef.current && !tagRef.current.contains(e.target)) {
        setExpanded(false);
      }
    };
    document.addEventListener('click', handleClick);
    return () => document.removeEventListener('click', handleClick);
  }, [expanded]);

  const confidencePercent = Math.round(entity.confidence * 100);
  const confidenceLabel =
    entity.confidence >= 0.85 ? 'High' :
    entity.confidence >= 0.6 ? 'Medium' :
    'Low';

  const humanType = entity.entity_type
    .replace(/_/g, ' ')
    .toLowerCase()
    .replace(/\b\w/g, c => c.toUpperCase());

  const reason = getReasonForType(entity.entity_type);

  return (
    <span className="relative inline-block mx-0.5" ref={tagRef}>
      {/* The tag itself */}
      <span
        className="pseudo-tag inline-block border-2 border-primary bg-surface-high font-[var(--font-mono)] text-xs font-bold px-2 py-1 neo-shadow-sm uppercase tracking-wide select-none"
        onClick={(e) => { e.stopPropagation(); setExpanded(!expanded); }}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => e.key === 'Enter' && setExpanded(!expanded)}
        title={`Click for details: ${humanType}`}
      >
        {entity.pseudonym}
      </span>

      {/* Expanded detail card */}
      {expanded && (
        <span className="popover-enter absolute bottom-full left-1/2 -translate-x-1/2 mb-3 w-72 bg-surface border-4 border-primary neo-shadow-lg p-0 z-50 flex flex-col">
          {/* Header */}
          <span className="flex items-center justify-between px-4 py-2 bg-primary text-on-primary">
            <span className="font-[var(--font-mono)] text-xs uppercase tracking-wider font-bold">
              {humanType}
            </span>
            <button
              onClick={(e) => { e.stopPropagation(); setExpanded(false); }}
              className="text-on-primary hover:opacity-70 text-lg font-bold cursor-pointer leading-none"
              aria-label="Close"
            >
              &times;
            </button>
          </span>

          {/* Body */}
          <span className="flex flex-col gap-3 px-4 py-3">
            {/* Confidence */}
            <span className="flex items-center justify-between">
              <span className="font-[var(--font-mono)] text-xs text-secondary uppercase">Confidence</span>
              <span className="flex items-center gap-2">
                <span className="font-[var(--font-mono)] text-sm font-bold">{confidencePercent}%</span>
                <span className={`font-[var(--font-mono)] text-xs px-2 py-0.5 border border-primary uppercase font-bold ${
                  confidenceLabel === 'High' ? 'bg-surface-high' : 'bg-surface'
                }`}>
                  {confidenceLabel}
                </span>
              </span>
            </span>

            {/* Confidence bar */}
            <span className="block w-full h-1.5 bg-surface-high border border-primary">
              <span
                className="block h-full bg-primary transition-all"
                style={{ width: `${confidencePercent}%` }}
              />
            </span>

            {/* WHY it was flagged */}
            <span className="block border-t-2 border-primary pt-3">
              <span className="block font-[var(--font-mono)] text-xs text-primary uppercase tracking-wider font-bold mb-1">
                Why flagged
              </span>
              <span className="block font-[var(--font-body)] text-sm text-on-background leading-relaxed">
                {reason}
              </span>
            </span>
          </span>

          {/* Caret */}
          <span className="absolute top-full left-1/2 -translate-x-1/2 w-3 h-3 bg-surface border-r-4 border-b-4 border-primary rotate-45 -mt-1.5" />
        </span>
      )}
    </span>
  );
}
