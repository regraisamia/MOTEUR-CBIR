import React from 'react'
import { User, MapPin, Stethoscope, Tag, Hash, Calendar } from 'lucide-react'

const rows = [
  { key: 'image_name',       label: 'Image ID',         icon: Hash },
  { key: 'patient_id',       label: 'Patient ID',        icon: User },
  { key: 'sex',              label: 'Sex',               icon: User },
  { key: 'age_approx',       label: 'Age',               icon: Calendar },
  { key: 'anatom_site',      label: 'Anatomical Site',   icon: MapPin },
  { key: 'diagnosis',        label: 'Diagnosis',         icon: Stethoscope },
  { key: 'benign_malignant', label: 'Classification',    icon: Tag },
]

export default function MetadataPanel({ metadata }) {
  if (!metadata) return null
  return (
    <table className="meta-table">
      <tbody>
        {rows.map(({ key, label, icon: Icon }) => {
          const val = metadata[key]
          if (!val && val !== 0) return null
          return (
            <tr key={key}>
              <td><span style={{ display: 'flex', alignItems: 'center', gap: 6 }}><Icon size={13} color="var(--text3)" />{label}</span></td>
              <td>
                {key === 'benign_malignant'
                  ? <span className={`badge ${val === 'malignant' ? 'badge-malignant' : 'badge-benign'}`}>{val}</span>
                  : String(val)
                }
              </td>
            </tr>
          )
        })}
      </tbody>
    </table>
  )
}
