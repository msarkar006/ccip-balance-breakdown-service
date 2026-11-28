import { useState, type FormEvent } from 'react';
import { Button, Select, SelectItem, TextArea, TextInput } from '@carbon/react';
import { ArrowRight } from '@carbon/icons-react';
import type { DataRightsRequestType } from '../../types/dataRights';
import './datarights.css';

export interface DataRightsFormValues {
  requestType: DataRightsRequestType;
  subjectRef?: string;
}

interface DataRightsFormProps {
  onSubmit: (values: DataRightsFormValues) => void;
  submitting: boolean;
  /** Administrators must name the subject; customers never send one. */
  requireSubject: boolean;
}

/** New-request form: request type (required), optional note (not sent), submit. */
export function DataRightsForm({ onSubmit, submitting, requireSubject }: DataRightsFormProps) {
  const [requestType, setRequestType] = useState('');
  const [note, setNote] = useState('');
  const [subjectRef, setSubjectRef] = useState('');
  const [typeInvalid, setTypeInvalid] = useState(false);
  const [subjectInvalid, setSubjectInvalid] = useState(false);

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    const missingType = requestType === '';
    const missingSubject = requireSubject && subjectRef.trim() === '';
    setTypeInvalid(missingType);
    setSubjectInvalid(missingSubject);
    if (missingType || missingSubject) return;
    onSubmit({
      requestType: requestType as DataRightsRequestType,
      ...(requireSubject ? { subjectRef: subjectRef.trim() } : {}),
    });
  };

  return (
    <form className="dr-form" noValidate aria-labelledby="dr-h" onSubmit={handleSubmit}>
      <h2 className="cds--productive-heading-03" id="dr-h">
        New request
      </h2>
      {requireSubject ? (
        <div className="dr-form__field">
          <TextInput
            id="req-subject"
            labelText="Subject reference"
            helperText="The customer reference the request is for."
            value={subjectRef}
            invalid={subjectInvalid}
            invalidText="Enter a subject reference."
            onChange={(event) => setSubjectRef(event.target.value)}
          />
        </div>
      ) : null}
      <div className="dr-form__field">
        <Select
          id="req-type"
          name="requestType"
          labelText="Request type"
          helperText="Export gives you a copy of the synthetic data held for you. Deletion asks for it to be removed once the request is reviewed."
          value={requestType}
          invalid={typeInvalid}
          invalidText="Choose a request type."
          onChange={(event) => setRequestType(event.target.value)}
        >
          <SelectItem value="" text="Choose a request type" />
          <SelectItem value="export" text="Export my data" />
          <SelectItem value="deletion" text="Delete my data" />
        </Select>
      </div>
      <div className="dr-form__field">
        <TextArea
          id="req-note"
          name="note"
          labelText="Note (optional)"
          helperText="Do not enter card numbers, bank details or passwords. Up to 250 characters."
          maxLength={250}
          value={note}
          onChange={(event) => setNote(event.target.value)}
        />
      </div>
      <Button type="submit" renderIcon={ArrowRight} disabled={submitting}>
        Submit request
      </Button>
    </form>
  );
}
