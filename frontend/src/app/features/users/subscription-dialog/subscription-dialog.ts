
import { Component, Inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { MatDialogRef, MAT_DIALOG_DATA, MatDialogModule } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatChipsModule } from '@angular/material/chips';
import { MatIconModule } from '@angular/material/icon';
import { MatSelectModule } from '@angular/material/select';
import { COMMA, ENTER } from '@angular/cdk/keycodes';
import { MatChipInputEvent } from '@angular/material/chips';
import { NotificationService } from '../../../core/services/notification.service';
import { User } from '../../../core/services/user.service';

@Component({
    selector: 'app-subscription-dialog',
    standalone: true,
    imports: [
        CommonModule,
        ReactiveFormsModule,
        MatDialogModule,
        MatFormFieldModule,
        MatInputModule,
        MatButtonModule,
        MatChipsModule,
        MatIconModule,
        MatSelectModule
    ],
    templateUrl: './subscription-dialog.html',
    styles: [`
    mat-form-field { width: 100%; margin-bottom: 8px; }
  `]
})
export class SubscriptionDialogComponent {
    form: FormGroup;
    therapeuticAreas: string[] = [];
    separatorKeysCodes: number[] = [ENTER, COMMA];
    availableChannels: string[] = ['EMAIL', 'SMS', 'IN_APP'];

    constructor(
        private fb: FormBuilder,
        public dialogRef: MatDialogRef<SubscriptionDialogComponent>,
        @Inject(MAT_DIALOG_DATA) public data: User
    ) {
        this.form = this.fb.group({
            competitorIds: [[]], // Simplified to just text input or multi-select if we had list
            channels: [['EMAIL'], Validators.required]
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
        if (this.form.valid && (this.therapeuticAreas.length > 0 || this.form.value.competitorIds.length > 0)) {
            // Prepare subscription object
            // NOTE: In a real app we'd map competitor names to IDs.
            // specific competitor selection is skipped for MVP in favor of just areas or manual ID entry if needed.
            // We'll stick to areas for now as primary filter.

            const subscription = {
                userId: this.data.id,
                therapeuticAreas: this.therapeuticAreas,
                competitorIds: [], // future: fetch competitors and allow selection
                channels: this.form.value.channels
            };
            this.dialogRef.close(subscription);
        }
    }

    onCancel(): void {
        this.dialogRef.close();
    }
}
