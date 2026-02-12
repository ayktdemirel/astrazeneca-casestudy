import { Component, Inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { MatDialogRef, MAT_DIALOG_DATA, MatDialogModule } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatChipsModule } from '@angular/material/chips';
import { MatIconModule } from '@angular/material/icon';
import { COMMA, ENTER } from '@angular/cdk/keycodes';
import { MatChipInputEvent } from '@angular/material/chips';
import { Competitor } from '../../../core/services/competitor.service';

@Component({
    selector: 'app-competitor-dialog',
    standalone: true,
    imports: [
        CommonModule,
        ReactiveFormsModule,
        MatDialogModule,
        MatFormFieldModule,
        MatInputModule,
        MatButtonModule,
        MatChipsModule,
        MatIconModule
    ],
    templateUrl: './competitor-dialog.html',
    styles: [`
    mat-form-field { width: 100%; margin-bottom: 8px; }
  `]
})
export class CompetitorDialogComponent {
    form: FormGroup;
    therapeuticAreas: string[] = [];
    separatorKeysCodes: number[] = [ENTER, COMMA];
    isEditMode = false;

    constructor(
        private fb: FormBuilder,
        public dialogRef: MatDialogRef<CompetitorDialogComponent>,
        @Inject(MAT_DIALOG_DATA) public data: Competitor | null
    ) {
        this.isEditMode = !!data;
        this.therapeuticAreas = data?.therapeuticAreas ? [...data.therapeuticAreas] : [];

        this.form = this.fb.group({
            name: [data?.name || '', [Validators.required]],
            headquarters: [data?.headquarters || ''],
            activeDrugs: [data?.activeDrugs || 0, [Validators.min(0)]],
            pipelineDrugs: [data?.pipelineDrugs || 0, [Validators.min(0)]]
        });
    }

    addArea(event: MatChipInputEvent): void {
        const value = (event.value || '').trim();
        if (value) {
            this.therapeuticAreas.push(value);
        }
        event.chipInput!.clear();
    }

    removeArea(area: string): void {
        const index = this.therapeuticAreas.indexOf(area);
        if (index >= 0) {
            this.therapeuticAreas.splice(index, 1);
        }
    }

    onSubmit() {
        if (this.form.valid) {
            const result: Competitor = {
                ...this.data, // Keep ID if editing
                ...this.form.value,
                therapeuticAreas: this.therapeuticAreas
            };
            this.dialogRef.close(result);
        }
    }

    onCancel(): void {
        this.dialogRef.close();
    }
}
